Make sure you have aws CLI installed in your bastion host.

Mostly in production EKS and RDS both Stays in private subnet. Only applications can talk to RDS.

And we will manage RDS and EKS from our bastion host.

In the bastion host make sure AWS CLI, kubectl and Helm is installed.

I have already the EKS cluster ready.

Run the following to create RDS database:

## 1️⃣ Create DB Subnet Group (PRIVATE subnets only)

> Use private subnet IDs (no route to Internet Gateway)
> 

```bash
aws rds create-db-subnet-group \
  --db-subnet-group-name pg-subnet-group \
  --db-subnet-group-description "Private subnets for PostgreSQL" \
  --subnet-ids subnet-0e2f78a932dfb1906 subnet-024b4ef71fb03688b \ #private subnets
  --region us-east-1
```

✔ Subnets must be in **different AZs**

---

## 2️⃣ Create Security Group for PostgreSQL

```bash
aws ec2 create-security-group \
  --group-name postgres-sg \
  --description "Postgres private access" \
  --vpc-id vpc-0c5ac3f5836072a0c \ #replace vpc id
  --region us-east-1
```

Fetch security group id

```bash
aws ec2 describe-security-groups \
  --filters Name=group-name,Values=postgres-sg \
  --query "SecurityGroups[0].GroupId" \
  --output text \
  --region us-east-1
```

### Allow access ONLY from your vpc cidr

(Recommended)

```bash
aws ec2 authorize-security-group-ingress \
  --group-id sg-05dde794de6c5a4b8 \
  --protocol tcp \
  --port 5432 \
  --cidr 10.0.0.0/16 \
  --region us-east-1
```

---

## List Supported PostgreSQL Versions (DO THIS)

Run this **once** and use the output:

```bash
aws rds describe-db-engine-versions \
  --engine postgres \
  --query"DBEngineVersions[].EngineVersion" \
  --output table \
  --region us-east-1
```

## 3️⃣ Create Private PostgreSQL RDS Instance

🚫 **No `--publicly-accessible` flag**

```bash
aws rds create-db-instance \
  --db-instance-identifier mlflow-postgres-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 17.6 \
  --allocated-storage 20 \
  --storage-type gp3 \
  --master-username postgres \
  --master-user-password MLflow123! \
  --db-name postgres \
  --vpc-security-group-ids sg-05dde794de6c5a4b8 \
  --db-subnet-group-name pg-subnet-group \
  --backup-retention-period 7 \
  --no-multi-az \
  --region us-east-1
```

✅ Result:

- **No public IP**
- DNS resolves only inside VPC
- Accessible from EC2/EKS/Lambda in same VPC

---

## 4️⃣ Verify It’s Private

```bash
aws rds describe-db-instances \
  --db-instance-identifier mlflow-postgres-db \
  --query "DBInstances[0].PubliclyAccessible" \
  --output text \
  --region us-east-1
```

Expected output:

```
false
```

---

Wait until its status is available:

```bash
aws rds wait db-instance-available \
  --db-instance-identifier mlflow-postgres-db \
  --region us-east-1
```

Get the RDS endpoint

```bash
aws rds describe-db-instances \
  --db-instance-identifier mlflow-postgres-db \
  --query "DBInstances[0].Endpoint.Address" \
  --output text \
  --region us-east-1
```

Install the postgres client on the bastion.

https://www.postgresql.org/download/

```bash
sudo apt install postgresql
```

## 5️⃣ How to Connect (Inside VPC)

### From EC2 / Bastion / Pod

```bash
psql \
  -h mlflow-postgres-db.chuc6ocm2qig.us-east-1.rds.amazonaws.com \
  -U postgres \
  -d postgres \
  -p 5432
```

### From your laptop?

❌ Not directly

✔ Options:

- Bastion host
- AWS SSM Session Manager
- VPN (Client VPN / Site-to-Site)
- EKS port-forward (if app inside cluster)

Prepare you database for MLflow:

```sql
CREATE DATABASE mlflow;
CREATE USER mlflow_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE mlflow TO mlflow_user;
```

Connect into new DB:

```bash
\c mlflow mlflow_user
```

Create schema:

```sql
CREATE SCHEMA mlflow;
```

Set default schema:

```sql
ALTER ROLE mlflow_userIN DATABASE mlflow
SET search_path= mlflow;
```

<aside>
💡

`GRANT ALL PRIVILEGES ON SCHEMA public TO mlflow_user;`

did not work because you are on **AWS RDS**, where:

- the `public` schema is owned by a **system-managed role**
- your user is **not allowed to create objects in it**
- RDS restricts schema ownership & CREATE permissions

So the GRANT **looked successful**, but CREATE was still blocked.

In a normal self-hosted PostgreSQL server, this command **does work** —

that’s why you see examples online where it succeeds.

Your case is different because of **RDS permission model**.

---

# 🧠 What happens behind the scenes

In vanilla PostgreSQL:

- `postgres` is a true superuser
- `public` is usually owned by that superuser
- superuser can grant anything

So this works:

```sql
GRANTALL PRIVILEGESON SCHEMA publicTO app_user;

```

and the user gets:

- USAGE
- CREATE
- etc.

---

# 🟡 But in AWS RDS

RDS removes full superuser rights.

Instead, RDS introduces this system role:

```
pg_database_owner

```

On RDS:

- `public` schema is owned by `pg_database_owner`
- your user does **not** own the schema
- even the DB admin is **not a real superuser**

So when you ran:

```sql
GRANTALL PRIVILEGESON SCHEMA publicTO mlflow_user;

```

Postgres evaluated:

- “this role does not own this schema”
- “and cannot delegate CREATE privileges”

Result:

- Some privileges may apply
- But **CREATE is NOT granted**
- And PostgreSQL only warns (not errors)

Which is why you saw:

```
WARNING:noprivileges were grantedfor "public"

```

But no hard failure.

The failure only appeared later when MLflow tried to:

```
CREATETABLEpublic.experiments

```

# Why it worked for other people

It works in environments where:

- database is self-hosted
- user has superuser rights
- or schema is actually owned by that user

For example:

Local Postgres docker / VM / on-prem:

✔ user is schema owner

✔ GRANT works normally

AWS RDS:

✘ restricted ownership

✘ CREATE not granted

✘ runtime failure

So both answers online are correct —

they just apply to **different environments**.

</aside>

<aside>
💡

### Verify schema + search path (Optional)

```sql
SELECTcurrent_schema(), current_setting('search_path');
```

Expected:

```
mlflow | mlflow
```

# **Final DB State After MLflow runs succesfully.**

```sql
\dt mlflow.*;
```

Tables present: (automatically created by MLflow )

- experiments
- runs
- metrics
- params
- tags
- etc.

# **What NOT to do on AWS RDS**

Avoid relying on:

```sql
GRANTALL PRIVILEGESON SCHEMA publicTO<user>;

```

Because on RDS:

- user does **not own** `public`
- GRANT may partially apply
- CREATE may still fail
- errors only appear at runtime

Or MLflow will crash.

</aside>

# Install MLflow

```bash
helm repo add community-charts https://community-charts.github.io/helm-charts
helm repo update
```

Create a namespace for mlflow

```bash
kubectl create ns mlflow
```

create a secret in that namespace:

```bash
kubectl create secret generic postgres-database-secret \
  --namespace mlflow \
  --from-literal=username=mlflow_user \
  --from-literal=password=MLflow123!
```

Get the values for mlflow helm chart:

```bash
helm show values community-charts/mlflow --version 1.8.1 > mlflow-values-1.8.1.yaml
```

edit the values file

```bash
vi mlflow-values-1.8.1.yaml
```

Add/Edit the following details to the respective blocks:

```bash
backendStore:
  # -- Specifies if you want to run database migration
  databaseMigration: true

  # -- Add an additional init container, which checks for database availability
  databaseConnectionCheck: false

  # -- Specifies the default sqlite path
  defaultSqlitePath: ":memory:"

  postgres:
    # -- Specifies if you want to use postgres backend storage
    enabled: true
    # -- Postgres host address. e.g. your RDS or Azure Postgres Service endpoint
    host: "mlflow-postgres-db.chuc6ocm2qig.us-east-1.rds.amazonaws.com" # required
    # -- Postgres service port
    port: 5432 # required
    # -- mlflow database name created before in the postgres instance
    database: "mlflow" # required
    # -- postgres database user name which can access to mlflow database
    user: "" # required
    # -- postgres database user password which can access to mlflow database
    password: "" # required
    # -- postgres database connection driver. e.g.: "psycopg2"
    driver: ""

  existingDatabaseSecret:
    # -- The name of the existing database secret.
    name: "postgres-database-secret"
    # -- The key of the username in the existing database secret.
    usernameKey: "username"
    # -- The key of the password in the existing database secret.
    passwordKey: "password"

```

Install the MLflow:

```bash
helm upgrade  -i mlflow community-charts/mlflow -n mlflow -f mlflow-values-1.8.1.yaml --version 1.8.1
```

Output:

```bash
Release "mlflow" does not exist. Installing it now.
NAME: mlflow
LAST DEPLOYED: Tue Dec 30 06:40:11 2025
NAMESPACE: mlflow
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
1. Get the application URL by running these commands:
  export POD_NAME=$(kubectl get pods --namespace mlflow -l "app.kubernetes.io/name=mlflow,app.kubernetes.io/instance=mlflow" -o jsonpath="{.items[0].metadata.name}")
  export CONTAINER_PORT=$(kubectl get pod --namespace mlflow $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl --namespace mlflow port-forward $POD_NAME 8080:$CONTAINER_PORT
```

Expose MLflow with ingress:

Install ingress controller:

```bash
helm repo add haproxytech https://haproxytech.github.io/helm-charts
helm repo update
```

```bash
helm install ha-proxy-ingress haproxytech/kubernetes-ingress \
  --set controller.service.type=LoadBalancer \
  --set controller.service.enablePorts.quic=false \
  --namespace haproxy \
  --create-namespace
```

Make sure its running:

```bash
kubectl get pods -n haproxy
```

output:

```bash
NAME                                                  READY   STATUS    RESTARTS   AGE
ha-proxy-ingress-kubernetes-ingress-8b9879d5d-f5zdv   1/1     Running   0          3m48s
ha-proxy-ingress-kubernetes-ingress-8b9879d5d-v7xtq   1/1     Running   0          3m32s
```

Check the external IP:

```bash
kubectl get svc -n haproxy
```

output:

```bash
NAME                                  TYPE           CLUSTER-IP       EXTERNAL-IP                                                               PORT(S)                                      AGE
ha-proxy-ingress-kubernetes-ingress   LoadBalancer   172.20.249.110   af194627aaa1a4d1882469e97176047c-1839362196.us-east-1.elb.amazonaws.com   80:30755/TCP,1024:32537/TCP,6060:30405/TCP   111m
```

Expose MLflow:

It is bit painful to expose the mlflow through ingress

<aside>
💡

## 1️⃣ How ingress and MLflow interact

- **Ingress controller** (HAProxy, Nginx, Traefik, etc.) sits **in front of MLflow**.
- Browser → Ingress → MLflow pod.

### Example:

- Browser requests: `https://mlflow-app.training.infypedia.org`
- Ingress sees the `Host: mlflow-app.training.infypedia.org` header
- Ingress forwards it to MLflow pod, usually on `http://mlflow:5000` (ClusterIP)

---

## 2️⃣ What MLflow sees

If MLflow is running on:

```
--host0.0.0.0
```

- It **binds to all network interfaces** inside the pod
- Doesn’t know about the “public hostname”
- It only sees **the Host header that was forwarded by ingress**

---

## 3️⃣ Why the “Invalid Host header” happens

- MLflow **by default enables a security middleware**
- It checks the **Host header** against allowed values (for DNS rebinding attack protection)
- If the Host header is **not recognized**, it rejects the request:

```
Rejected requestwith invalid Hostheader: mlflow-app.training.infypedia.org
```

Even though:

- The hostname in browser is correct
- The pod is listening on 0.0.0.0

Because **MLflow’s middleware only allows “localhost” or explicitly specified allowed hosts**.

---

## 4️⃣ Two ways to fix this

### Option A — Keep security middleware

- Pass the hostname MLflow should accept via **`-allowed-hosts`**
- Must use **uvicorn server**, not gunicorn

### Option B — Disable security middleware

- Add **`-disable-security-middleware`** (works with gunicorn)
- Let ingress handle host validation
- Easiest in Kubernetes

I will use the Option B here below 
log set to false to activate option B and add the —allowed ports through extra args.
</aside>

Edit the mlflow values file:

```bash
vi mlflow-values-1.8.1.yaml 
```

Go to the ingress section:

```bash
ingress:
  # -- Specifies if you want to create an ingress access
  enabled: true
  # -- New style ingress class name. Only possible if you use K8s 1.18.0 or later version
  className: "haproxy"
  # -- Additional ingress annotations
  annotations: {}
    # kubernetes.io/ingress.class: nginx
    # kubernetes.io/tls-acme: "true"
  hosts: 
    - host: mlflow-app.training.infypedia.org
      paths:
        - path: /
          # -- Ingress path type
          pathType: Prefix

```

Set the log for ingress to work:

```bash
log:
  # -- Specifies if you want to enable mlflow logging.
  enabled: false
  # -- Mlflow logging level.
  level: info
```

Set the extra arguments for ingress:

```bash
extraArgs:
  allowedHosts: "mlflow-app.training.infypedia.org"
  corsAllowedOrigins: "*"
```

Upgrade the app now:

```bash
helm upgrade  -i mlflow community-charts/mlflow -n mlflow -f mlflow-values-1.8.1.yaml --version 1.8.1 
```

output:

```bash
Release "mlflow" has been upgraded. Happy Helming!
NAME: mlflow
LAST DEPLOYED: Tue Dec 30 10:33:42 2025
NAMESPACE: mlflow
STATUS: deployed
REVISION: 2
TEST SUITE: None
NOTES:
1. Get the application URL by running these commands:
  http://mlflow-app.training.infypedia.org/
```

Bind the host with the load balancer dns in you dns zone and access the app in the browser.

In the second step its good practise to protect your mlflow in production , You can use LDAP authentication with SSO or you can go for basic authentication.

Basic Authentication:

Dont hardcode your creds in the values or config file always use kubernetes secrets:

```bash
kubectl create secret generic mlflow-auth \
  --namespace mlflow \
  --from-literal=admin-user=admin \
  --from-literal=admin-password=your-secure-password
```

Edit the values file and add the following in the auth section.

```bash
auth:
  # -- Specifies if you want to enable mlflow authentication. auth and ldapAuth can't be enabled at same time.
  enabled: true
  # -- Mlflow admin user username
  adminUsername: "mlflow"
  # -- Mlflow admin user password
  adminPassword: "mlflow12345!"
  # -- Specifies if you want to use an existing admin credentials secret for auth. If it's set, adminUsername and adminPassword will be ignored.
  existingAdminSecret:
    # -- The name of the existing admin credentials secret.
    name: "mlflow-auth"
    # -- The key of the admin username in the existing admin credentials secret.
    usernameKey: "admin-user"
    # -- The key of the admin password in the existing admin credentials secret.
    passwordKey: "admin-password"
  # -- Default permission for all users. More details: https://mlflow.org/docs/latest/auth/index.html#permissions
```

Upgrade the MLflow helm deployment:

```bash
helm upgrade  -i mlflow community-charts/mlflow -n mlflow -f mlflow-values-1.8.1.yaml --version 1.8.1 
```

Access the app using the FQDN and it should ask username and password.

Similarly you can configure with your LDAP and SSO as well. 

 

<aside>
💡

Basic auth and ldapAuth can't be enabled at same time.

</aside>
