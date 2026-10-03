import httpx
import time

API_BASE = "http://localhost:8000/api/v1"

def main():
    print("Connecting to backend at", API_BASE)
    with httpx.Client(base_url=API_BASE) as client:
        # 1. Register a test user
        print("Registering user...")
        resp = client.post("/auth/register", json={
            "email": f"test_{int(time.time())}@example.com",
            "username": "test_creator",
            "password": "password123"
        })
        
        # It's okay if user exists, we will just login
        if resp.status_code == 409:
            resp = client.post("/auth/login", json={
                "email": "test_creator@example.com",
                "password": "password123"
            })
            
        token = resp.json().get("access_token")
        client.headers.update({"Authorization": f"Bearer {token}"})
        
        # 2. Create a project
        print("Creating project...")
        proj_resp = client.post("/projects", json={
            "title": "My First AI Video",
            "topic": "The History of AI",
            "tone": "educational",
            "duration": "short"
        })
        
        if proj_resp.status_code >= 400:
            print("Failed to create project:", proj_resp.text)
            return
            
        project_id = proj_resp.json()["id"]
        print(f"Project created with ID: {project_id}")
        
        # 3. Generate script
        print("Generating script...")
        client.post(f"/generate/script/{project_id}")
        
        # 4. Generate visuals
        print("Generating visuals...")
        client.post(f"/generate/visuals/{project_id}")
        
        # 5. Generate narration
        print("Generating narration...")
        client.post(f"/generate/narration/{project_id}")
        
        # 6. Render video
        print("Rendering video...")
        job_resp = client.post(f"/generate/render/{project_id}")
        job_id = job_resp.json()["id"]
        print(f"Render job started with ID: {job_id}")
        
        # Poll for completion
        while True:
            status_resp = client.get(f"/generate/jobs/{job_id}")
            status = status_resp.json()["status"]
            print(f"Job status: {status}")
            if status in ["completed", "failed"]:
                break
            time.sleep(2)
            
        print("Video generation finished!")
        print(f"Check the frontend dashboard to view your video: http://localhost:3000/dashboard")

if __name__ == "__main__":
    main()
