# Quick Start Guide

## First Time Setup (5 minutes)

### 1. Install Dependencies

```bash
cd /home/tpolson/cloud
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the Application

```bash
streamlit run app.py
```

The app will open in your browser at http://localhost:8501

### 3. Configure Credentials

**For AWS:**
1. Click **Settings** in the sidebar
2. Go to **AWS Credentials** tab
3. Enter your Access Key ID and Secret Access Key
4. Select your default region
5. Check **"Remember credentials"** ✅
6. Click **"Save AWS Credentials"**
7. Click **"Test Connection"** to verify

**For GCP:**
1. Click **Settings** in the sidebar
2. Go to **GCP Credentials** tab
3. Enter your Project ID
4. Upload or paste your service account JSON key
5. Select your default zone
6. Check **"Remember credentials"** ✅
7. Click **"Save GCP Credentials"**
8. Click **"Test Connection"** to verify

### 4. Start Provisioning!

Go back to **Home** and create your first resource:

**AWS EC2 Example:**
- Provider: AWS
- Resource: Virtual Machine
- Name: my-first-server
- Instance Type: t2.micro
- Click: 🚀 Provision EC2 Instance

**GCP Compute Example:**
- Provider: GCP
- Resource: Virtual Machine
- Name: my-first-server
- Machine Type: e2-micro
- Click: 🚀 Provision GCE Instance

### 5. Manage Your VMs

Click **VM Management** in the sidebar to:
- ⏸️ Stop/▶️ Start instances
- 🔄 Reboot instances
- 📎 Attach storage volumes
- 🔐 Get SSH commands
- 🗑️ Terminate instances

## Next Steps

- Read [CREDENTIALS.md](CREDENTIALS.md) for security best practices
- Check [README.md](README.md) for advanced features
- See [docs/VM_MANAGEMENT.md](docs/VM_MANAGEMENT.md) for detailed VM operations

## Quick Tips

✅ **Enable "Remember credentials"** - Your credentials are encrypted and auto-loaded  
✅ **Test connections first** - Verify credentials before provisioning  
✅ **Use the Settings page** - Easier than environment variables  
✅ **Check VM Management** - Monitor all your instances in one place  

## Troubleshooting

**App won't start?**
```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

**Credentials not loading?**
- Check that "Remember credentials" is enabled
- Look for `~/.cloud-automation/credentials.enc`
- Try clearing and re-saving credentials

**Can't connect to cloud?**
- Click "Test Connection" in Settings
- Check IAM permissions (AWS) or service account roles (GCP)
- Verify your credentials are correct

## Default Locations

| Item | Location |
|------|----------|
| Virtual Environment | `/home/tpolson/cloud/.venv` |
| Encrypted Credentials | `~/.cloud-automation/credentials.enc` |
| App Entry Point | `/home/tpolson/cloud/app.py` |
| Settings Page | `http://localhost:8501` → Settings |

## Getting Help

- 📖 [Full Documentation](README.md)
- 🔐 [Credential Guide](CREDENTIALS.md)
- 🖥️ [VM Management Guide](docs/VM_MANAGEMENT.md)

Happy provisioning! ☁️
