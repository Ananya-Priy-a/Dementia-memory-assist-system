# Dementia Memory Assist System

## 📌 Project Overview

The **Dementia Memory Assist System** is a smart healthcare assistance application developed to support dementia and Alzheimer’s patients in managing their daily activities more independently. The system helps users remember medications, appointments, and routine tasks through reminders and notifications while also allowing caregivers to monitor patient activities and receive emergency alerts.

This project focuses on improving patient safety, reducing dependency on caregivers, and providing a user-friendly interface suitable for elderly users.

---

# 🚀 Features

- 🔔 Medication reminders
- 📅 Daily task scheduling
- 🆘 Emergency SOS alerts
- 📍 Location tracking support
- 👨‍⚕️ Caregiver notifications
- 🎤 Voice assistance
- 📱 Responsive user interface
- 🔒 Secure patient data handling

---

# 🛠️ Tech Stack

## Frontend
- HTML
- CSS
- JavaScript

## Backend
- Node.js
- Express.js

## Database
- MongoDB

## Tools & Platforms
- Git
- GitHub
- VS Code

---

# 📂 Project Structure

```bash
Dementia-Memory-Assist-System/
│
├── client/                 # Frontend files
│   ├── public/
│   └── src/
│
├── server/                 # Backend files
│   ├── routes/
│   ├── models/
│   ├── controllers/
│   └── config/
│
├── package.json
├── README.md
└── .env
```

---

# ⚙️ Installation Guide

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/Dementia-Memory-Assist-System.git
```

Move into the project directory:

```bash
cd Dementia-Memory-Assist-System
```

---

## 2. Install Dependencies

Install all required dependencies:

```bash
npm install
```

If frontend and backend are separated:

```bash
cd client
npm install

cd ../server
npm install
```

---

## 3. Setup Environment Variables

Create a `.env` file inside the `server` folder and add the following:

```env
PORT=5000
MONGO_URI=your_mongodb_connection_string
JWT_SECRET=your_secret_key
```

Example MongoDB local connection:

```env
MONGO_URI=mongodb://127.0.0.1:27017/dementia_assist
```

---

# 🗄️ Database Setup

## MongoDB Local Setup

1. Install MongoDB on your system
2. Start MongoDB service
3. Add the MongoDB connection string in the `.env` file

---

# ▶️ Running the Project

## Start Backend Server

```bash
cd server
npm start
```

or for development mode:

```bash
npm run dev
```

---

## Start Frontend

```bash
cd client
npm start
```

---

# 🌐 Application URLs

Frontend:

```bash
http://localhost:3000
```

Backend:

```bash
http://localhost:5000
```

---

# 📸 Screenshots

Add screenshots of your project here.

Example:

```md
![Home Page](screenshots/home.png)
![Dashboard](screenshots/dashboard.png)
```

---

# 🔮 Future Enhancements

- AI-based patient health prediction
- Smart wearable device integration
- Multi-language support
- Cloud backup support
- Improved voice assistant features

---

# 🤝 Contribution

Contributions are welcome.

## Steps to Contribute

1. Fork the repository
2. Create a new branch

```bash
git checkout -b feature-name
```

3. Commit your changes

```bash
git commit -m "Added new feature"
```

4. Push to GitHub

```bash
git push origin feature-name
```

5. Create a Pull Request

---

# 🧪 Testing

Run tests using:

```bash
npm test
```

---

# 📄 License

This project is licensed under the MIT License.

---

# 👨‍💻 Author

**Abhii** 
Interested in healthcare technology and software development.

---

# ⭐ Support

If you found this project useful, please give it a ⭐ on GitHub.
