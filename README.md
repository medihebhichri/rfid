# Employee Management System
## RFID Access Control & Face Recognition System

**Author: Med Iheb Hichri**

## Legal Notice

**PROPRIETARY SOFTWARE**

This software, including all source code, documentation, hardware designs, and associated materials, is the exclusive intellectual property of Med Iheb Hichri. All rights are reserved.

**UNAUTHORIZED USE STRICTLY PROHIBITED**

Any unauthorized access, reproduction, distribution, modification, reverse engineering, or use of this system or its code without explicit written permission from the author is strictly prohibited and will result in legal consequences. This includes but is not limited to:

- Copying or reproducing any part of the code
- Modifying or creating derivative works
- Using the code or concepts in other projects
- Distributing the code to third parties
- Removing or altering this notice

**COPYRIGHT © 2025 MED IHEB HICHRI**

## System Overview

This integrated employee management system combines RFID access control with facial recognition technology to provide secure access management and comprehensive HR functionality. The system offers:

- Secure door access control using RFID verification
- Secondary authentication via facial recognition
- Employee attendance tracking and reporting
- HR management portal for employee data management
- Real-time access monitoring and alerts

## Components

The system consists of the following major components:

1. **Hardware**
   - ESP32 microcontroller
   - MFRC522 RFID reader
   - I2C LCD display (16x2)
   - Servo motor for door control
   - Status LEDs (red/green)
   - Camera module for facial recognition

2. **Software**
   - ESP32 firmware for RFID reading and access control
   - PyQt-based server application for authentication and management
   - Face recognition processing module
   - Employee database management system
   - Web interface for HR staff

## Technical Information

The system operates by:
1. Reading employee RFID cards via the MFRC522 module
2. Transmitting card data via WiFi to the central server
3. Verifying credentials against the employee database
4. Optionally conducting facial recognition for enhanced security
5. Controlling physical access through servo-operated mechanisms
6. Logging all access attempts and employee activities

## Contact Information

For inquiries regarding licensing, customization, or authorized use, please contact:

**Med Iheb Hichri**  
[Contact information redacted for privacy]
phone:+216 26653671
Mail:hichri.iheb13@gmail.com

---

**ALL RIGHTS RESERVED**  
This software is protected by copyright law and international treaties.  
Unauthorized reproduction or distribution may result in severe civil and criminal penalties.
