# iot_streams

The files in this directory are **not versioned** (`.gitignore`) because they contain SQL queries related to the **ASM Terni** database.

Specifically, one of the queries exposes a **partial structure of their database**.  
For confidentiality and compliance reasons, **we cannot share or publish these files** until we receive the official **disclosure approval from ASM Terni**.

---

## Deployment status

- The service has been deployed on the **NEMO cluster**, but the deployment is currently **scaled to 0 replicas**.  
- This decision was made because the service generated **errors impacting other pods** within the cluster.  
- The deployment configuration is set to **fetch the container image from a private registry** owned and maintained by Martel Innovate.  

---

Once official approval is granted:  
- The files will be removed from `.gitignore`  
- They can be properly versioned and included in the repository  
- The deployment will be re-enabled and scaled appropriately  

Until then:  
- The files must remain **local only**  
- They must **not be pushed or shared** with any third party
