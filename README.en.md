# 🛡️ Connection Vault

[繁體中文](README.md) | [简体中文](README.zh-CN.md) | [English](README.en.md)

A lightweight, containerized Web application designed for SI (System Integration) teams, IT operators, and Home Lab enthusiasts managing multiple Hyper-V or Kubernetes (K8s) nodes. Say goodbye to scattered spreadsheets and manage all your server, VM, and network device connection credentials in one secure, centralized vault.

## 🌟 Key Features

* 🔄 **Batch Import & Export:** One-click CSV import. Automatically creates new groups or updates existing device credentials.
* 🔍 **Smart Global Search:** Real-time filtering by group, device name, IP, or username.
* 🔒 **Security First:** Admin authentication, default password masking, and accidental deletion prevention.
* 🌗 **Modern UI:** Clean accordion-style interface with Dark/Light mode toggle.

## 🐳 Quick Start

Ensure Docker and Docker Compose are installed on your host.

**1. Clone the Repository**
```bash
git clone [https://github.com/YOUR_USERNAME/client-manager.git](https://github.com/YOUR_USERNAME/client-manager.git)
cd client-manager
```

**2. Configure Environment**
Copy the template and set your preferred port and admin credentials:
```bash
cp .env.example .env
```

**3. Deploy**
```bash
docker compose up -d
```
🎉 **Access:** Open your browser and navigate to `http://<Host-IP>:<Port>`. All data is securely persisted in the `./data` directory.

## 🔄 CSV Import Rules

When using the built-in Import feature, please adhere to the following:
1. **Format:** Only `.csv` files with **UTF-8 BOM** encoding are supported (we highly recommend downloading the Template directly from the Web UI).
2. **Update Mechanism:** If an imported row matches an existing "Group + Device Name", the system will automatically overwrite and update the credentials with the new data.

---

## 🤖 About the Development (Vibe Coding)

This project was brought to life using **Vibe Coding**—a collaborative development approach between a human architect and an AI assistant. This modern workflow allows the focus to remain strictly on system architecture, operational pain points, and user experience, while leveraging AI for rapid and efficient code implementation.