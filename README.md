### PROJECT CONVERTED FROM DOCKER-FILES TO K8S Manifests.

The files in this folder, feature a modular, Kubernetes data platform designed for deployment on an Amazon EKS (Elastic Kubernetes Service) cluster. It ingests, transforms, stores, secures, and analyzes data captured from IoT sources in real time.

The architecture is built around microservices deployed using Kustomize, enabling granular control over each component and its dependencies.

![Alt text](/images/EROS4NRG-architecture.svg)

The platform is composed of the following core modules:

*   **IoT Stream**: Captures live data from APIs or databases and loads it into a data lake.
    
*   **Data Pipeline**: Transforms and restructures raw data into metadata and data tables, storing the result in PostgreSQL.
    
*   **Data Catalogue**: A FastAPI-based microservice to expose structured data via a REST API.
    
*   **Predictive Analysis**: Offers forecasting capabilities using Facebook Prophet, MLP, and CatBoost.
    
*   **Keycloak**: Secures access with centralized identity and access management.
    

📚 Table of Contents
--------------------
    
1.  [Project Structure](#Project-Structure)
    
2.  [Installation](#Installation)
    
3.  [Usage](#Usage)

4.  [Configuration](#Configuration)
    
5.  [Docker Images](#Docker-Images)


# Project-Structure

The Kubernetes manifests are organized using kustomize, allowing modular deployment of each component. 
Here's a high-level view of the folder structure:
```
k8s/
├── deploy/
|   ├── grafana_provisioning/
│   |    ├── dashboards-config.yaml
|   |    └── datasources.yaml
│   ├── data-catalogue.yaml
│   ├── keycloak.yaml
│   ├── kustomization.yaml
|   ├── data-pipeline.yaml
|   ├── grafana.yaml
|   ├── iot-stream.yaml
|   ├── minio.yaml
|   ├── postgres.yaml
|   └── training-environment.yaml
├── svc/
│   ├── data-catalogue.yaml
│   ├── keycloak.yaml
│   ├── kustomization.yaml
|   ├── data-pipeline.yaml
|   ├── grafana.yaml
|   ├── iot-stream.yaml
|   ├── minio.yaml
|   ├── postgres.yaml
|   └── training-environment.yaml
├── pvcs/
│   ├── keycloak.yaml
│   ├── iotdata.yaml
│   ├── postgres.yaml
│   └── kustomization.yaml
├── secrets/
|    ├── postgres.yaml
|    ├── keycloak.yaml
|    ├── grafana.yaml
|    ├── minio.yaml
|    ├── docker.yaml
│    └── kustomization.yaml
├── storageclass/
|    ├── aws-sc.yaml
│    └── kustomization.yaml
├── namespace/
|    ├── nemo.yaml
│    └── kustomization.yaml
├── ingressclass/
|    ├── ingressclass.yaml
│    └── kustomization.yaml
├── ingress/
|    ├── ingress.yaml
│    └── kustomization.yaml
└── kustomization.yaml
```


### Deployment Order

When using Kustomize overlays, deploying the root `kustomization.yaml` file will do the magic.
Kustomize will sort and organize the resources in the correct order for you.
Hereafter, you can find the order if you prefer to proceed manual, piece meal.

1.  **Namespace**

2.   **Storage Class**
    
3.  **Persistent Volumes**

4. **Secrets**
    
5.  **PostgreSQL**
    
6.  **Keycloak**

7.  **Grafana**
    
8.  **IoT Stream**
    
9.  **Data Pipeline**
    
10.  **Data Catalogue**
    
11.  **training-environment**  # Predictive Analysis

12. **IngressClass**

13. **Ingress**



# Installation

> **Prerequisites**:
> 
> *   AWS EKS cluster configured and accessible via kubectl
>     
> *   kubectl and kustomize installed
>     
> *   IAM roles, EBS CSI driver, and necessary AWS permissions in place.
>
> As part of the AWS setup, we created dedicated IAM entities (roles, policies, and service accounts) to grant the required permissions for each component running in the EKS cluster.
>Where possible, IRSA (IAM Roles for Service Accounts) has been leveraged, ensuring that pods only receive the exact permissions they need without relying on node-level IAM roles.
>This improves security, auditability, and follows AWS best practices.
>     

For more information concerning the AWS K8s exposure, please visit the [AWS official Docs](https://aws.amazon.com/blogs/containers/exposing-kubernetes-applications-part-1-service-and-ingress-resources/) 


The manual installation can be done using the usual `kubectl apply -f filename.yaml`.


### 1\. Clone the Repository

`$ git clone https://github.com/martel-innovate/eros4nrg-k8s.git`

For the Kustomize deployment, just `cd` into the cloned repo and issue `kubectl apply -k kustomization.yaml` while for the manual installation, follow the steps below:


### 2\. Deploy the Namespace and StorageClass

`   kubectl apply -k namespace/   ` or `   kubectl apply -f namespace/nemo.yaml   `

`   kubectl apply -k storageclass/   ` or `   kubectl apply -f storageclass/aws-sc.yaml   `

This step sets up:

*   nemo namespace
    
*   EBS-backed StorageClass
    

### 3\. Apply Persistent Volume Claims

`   kubectl apply -k pvcs/` or `   kubectl apply -f pvcs/[filename].yaml   `

### 4\. Deploy Components One at a Time 


### Using `kubectl apply -f filename.yaml`

```
Example:
#################################################
##### Deploy PostgreSQL Deploy + svc + PVC: #####
#################################################

$ kubectl apply -f pvcs/postgres.yaml

$ kubectl apply -f deploy/postgres.yaml

$ kubectl apply -f svc/postgres.yaml
```

Whether you'd like to deploy pieces of infrastructure using Kustomize, you can create a new kustomization.yaml file at the repo's root (replacing the default one which is complete -- can be done issuing `mv kustomization.yaml kustomization.yaml.bak && touch kustomization.yaml`) and tweak the newly created file as per your needs.

```
Example:
#################################################
##### Deploy PostgreSQL Deploy + svc + PVC: #####
#################################################

apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: nemo

resources:
- deploy/
- secrets/
- pvcs/
- namespace/
- svc/
```
And in each kustomization file in sub-folders we'll add/remove the required resources.

### Example (pvcs/kustomization.yaml)

```
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- postgres.yaml
```

### Example (svc/kustomization.yaml)

```
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- postgres.yaml
```

### Example (deploy/kustomization.yaml)

```
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- postgres.yaml
```

And so on for every other subfolder.

Kustomize enables us to logically split our project in modules for better and granular deployments, enabling clarity and improving maintenance activities.


# Usage

Once deployed, the platform operates as follows:

1.  **IoT Stream** pulls real-time data from APIs or databases and loads it into the data lake.
    
2.  **Data Pipeline** transforms, cleans, and loads structured data into PostgreSQL.
    
3.  **Data Catalogue** provides an HTTP API (via FastAPI) to query stored datasets.
    
4.  **Predictive Analysis** uses models like Prophet, MLP, and CatBoost to forecast trends.
    
5.  **Keycloak** governs access to APIs and services with secure authentication flows.
    

To access services:

*   Use the **Ingress** controller endpoint for external access.
    
*   Query the **Data Catalogue** API at /api/v1/
    
*   Authenticate users or services via the **Keycloak** login endpoint.

If you have historical data to import, there are several ways for doing that:

1. Use `kubectl cp` to copy the .sql or .dump file into the postgres pod
2. Mount the file on the postgres volume.
3. Mount the file using ConfigMaps.

Whatever choice you make, once the file is uploaded, get a shell into the pod

`$ kubectl -n nemo exec -it podname -- sh`

and issue

`$ psql -U admin -d data < yourdump.sql`

For more info, please visit the [PostgreSQL official docs](https://www.postgresql.org/docs/8.1/backup.html)
    

# Configuration

The platform relies on a few key configuration areas across Kubernetes and service-level settings:

### 1\. **Namespace**

All components are deployed under the nemo namespace:

```
apiVersion: v1
kind: Namespace
metadata:
  name: nemo
```

### 2\. **Storage Class (EBS)**

A dynamic storage class is configured to provision EBS volumes for stateful services like PostgreSQL:

```
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-auto-sc
provisioner: ebs.csi.eks.amazonaws.com
volumeBindingMode: WaitForFirstConsumer
parameters:
  type: gp2
  fsType: ext4
  encrypted: "true"
allowVolumeExpansion: true
```

### 3\. **Secrets & Environment Variables**

*   Database credentials, Service account's pwds, and Keycloak secrets and Docker pvt registry token should be provided using Kubernetes **Secrets**.
    
*   Each deployment file may include envFrom or env definitions to inject config into pods.
    

### 4\. **Ingress & Service Exposure**

In this deployment we rely on the **AWS Application Load Balancer (ALB) Ingress Controller**, which automatically provisions an ALB and configures it to expose Kubernetes services to the outside world.
The ALB handles:

- HTTP/HTTPS termination (with support for AWS ACM-managed SSL certificates).

- Path and host-based routing to backend services (e.g., Grafana, Data Catalogue).

- Integration with AWS security groups and IAM for fine-grained access control.

**If you deploy this stack outside AWS, make sure to replace the ALB Ingress Controller with a different implementation (e.g., NGINX Ingress Controller) and adapt the annotations accordingly.**

Our Ingress exposes `grafana` and `data catalogue` (FastAPI).


# Docker-Images

Each component is containerized and should be built and pushed to a container registry (e.g., ECR, Docker Hub).
Note that those images (in our scenario) are hosted on a private registry and this is why we use 

```
imagePullSecrets:
        - name: marco-regcred
```
in our deployments. 

Make sure you replace that with your own image pull secret.

### ⚠️ Each image should:


*   Expose required ports (e.g., 8003 for FastAPI)
    
*   Use minimal base images with specific versions (not latest)
    
*   Be secured with non-root users where possible
