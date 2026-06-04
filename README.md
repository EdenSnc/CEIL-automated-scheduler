# CEIL Academic Scheduler

A high-performance automated scheduling and constraint-satisfaction engine built specifically for academic environments. This tool replaces manual, error-prone timetable construction with a robust CP-SAT optimization pipeline.

## 🚀 Overview
The **CEIL Scheduler** simplifies the complex task of aligning group schedules, teacher availability, room capacity, and language proficiency tiers. By leveraging Google's OR-Tools, the system generates optimized timetables that minimize gaps and conflicts while balancing teacher workloads.

## ⚙️ Key Features
* **Constraint-Based Optimization:** Built on Google OR-Tools to solve complex scheduling logic efficiently.
* **Responsive PyQt6 UI:** A high-performance GUI allowing for real-time CRUD operations, interactive scheduling views, and visual feedback.
* **Hardware-Aware Performance:** The engine dynamically calibrates thread allocation based on the host machine's core count, ensuring system stability on both modern workstations and older institutional hardware.
* **Intuitive Color-Coded Interface:** A clear, flag-inspired, and CEFR-tiered color coding system for instant visual recognition.
* **Persistent Storage:** Seamless JSON-based data persistence with integrated activity logging.

## 🛠️ Tech Stack
* **Language:** Python 3.10+
* **GUI Framework:** PyQt6 (Modern, responsive design with custom style-sheeting)
* **Optimization Engine:** Google OR-Tools (CP-SAT Solver)
* **Data Management:** JSON-based schema 

## 🏗️ Project Architecture
The project follows a clean Model-View-Controller (MVC) pattern to ensure high maintainability:
- **Models:** Handles data persistence and the mathematical constraint engine.
- **Views:** Built with custom PyQt6 widgets and high-contrast color palettes.
- **Controllers:** Orchestrates business logic, threading, and data synchronization.

## 🚀 Quick Start
1. Clone the repository: `git clone [YOUR-REPO-URL]`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python main.py`

## 📊 Optimization Engine
The scheduling engine uses a pre-solved matrix of constraints to generate valid timetables in under 45 seconds on standard hardware, with dynamic thread management to ensure system responsiveness during intensive calculations.

---
*Developed for the CEIL Language Learning Center.*
