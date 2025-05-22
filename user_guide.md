
---
Welcome to the cSDTM Quality Checks application. This guide explains how to navigate the app and use its key features.


## 1. Dashboard Overview

When you first open the app, you’ll see the main dashboard which includes:

- **Header Area:**  
At the very top, the header isn’t just about displaying our branding—it’s a control center designed to enhance the user navigation and overall experience. Here’s a closer look at the key buttons featured in the header:

- **Home Button:**  
  This button, typically shown with a house icon, immediately takes you back to the main landing page. It’s your go‑to shortcut for starting fresh whenever you need to abandon the current workflow or begin a new analysis.

- **Back Button:**  
  When you need to reverse your steps and return to the previous view, the Back button (indicated by an arrow icon) provides a simple way to navigate backward throughout the app. It saves you the hassle of manual URL changes or multiple clicks.

- **Info Button:**  
  The Info button (featured with an info-circle icon) is your quick access to context-sensitive guidance. Clicking this button opens a popup that offers insights, clarifications, and additional data-related tips about quality checks. It helps demystify any ambiguous results and directs you to relevant documentation or support.

- **User Guide Button:**  
  For a comprehensive walkthrough, the User Guide button (often paired with a book icon) opens a detailed guide in a popup window. This guide covers everything from how to navigate between pages to understanding the nuances of the quality check results, ensuring that you can make full use of the app’s features.

Together, these buttons create an intuitive, user-friendly header that not only presents our branding but also significantly improves navigation, support, and usability throughout the application.

- **Navigation and Content Area:**  
  The central area of the app is designed to display protocols first. All available protocols are shown so that you can choose one for more detailed information. Once you select a protocol, the content dynamically updates and you may also see:
  - **Project, Analysis Task and Analysis-Version Page:** Where you select the relevant project analysis task and analysis version.
  - **Checks Page:** Where detailed quality check results are presented in a table format and graphical representation of Status of checks, status of SDTM programs, Log issues and Number of checks perfromed on each dataset. 


- **Interactive Popups:**  
  The app utilizes popups for:
  - **Query Submission:** Allowing you to submit queries or checks to perfom on the SDTM datasets regarding the quality checks.
  - **User Guide:** Which explains how the app functions (this guide).

---

## 2. How to Navigate the Application

When you launch the app, start by selecting a protocol from the protocols section in the central area. Once you click on your selected protocol, the app will take you to the project area where you can choose the necessary project. After making a project selection, you will be directed to the analysis task area. Here, pick the task you wish to perform, and then you will be navigated to the analysis version page. At this stage, choose the version that meets your requirements, and the app will run the corresponding quality checks and display the results.


### URL Navigation
- **Direct URL Changes:**  
  You can also navigate by entering specific URLs:
  - **Protocol Selection:** The base URL displays the list of available protocols.
  - **Project/Analysis Task:** Once a protocol is selected, you can navigate further to view the associated projects and tasks.
  - **Display Table:** Detailed quality check results appear on the display table page when you select a specific analysis task and version.

### Query Submission
- **Submit Query Popup:**  
  A “Submit Query” button is available on the right side of the header. Clicking this button opens a popup form where you can enter the following information:
  - Your name, email, and domain.
  - A detailed description of your query or check, including the domain for which the query or checks are written.
  - Any associated rule or code.
  
  Once you click “Submit,” your query is sent to the system and will be incorporated in the next release.

- **Clipboard Copy (Copy Path Feature):**  
  For detailed checks to drill into subject information, you can copy the file path leading to the quality_checks_xx.xlsx file. This file contains more in-depth data.

---


## 3. Checks Page Details

On the Checks Page, you will find the following visualizations and features:

- **Status of Checks Pie Plot:**  
  A pie chart displays the overall status of quality checks, showing the percentage of checks that have passed, failed, or fall into other categories.

- **Status of SDTM Programs:**  
  Underneath the pie plot, you will see a chart that pulls information from the SPTracker. This visualization shows the percentage of programming completed in the current analysis task/version folder.

- **Number of Checks Performed Across the Datasets:**  
  A bar chart illustrates the number of checks performed for each domain (or combination of domains).

- **Log Issues Donut Plot:**  
  A donut plot displays the percentage of log issues found in the analysis task/version folder, helping you quickly assess the severity of log issues.

- **Detailed Checks Table:**  
  The table below the plots provides a detailed breakdown of checks performed on each dataset. For any dataset that fails a check, additional notes are displayed.

- **Clipboard Copy (Copy Path Feature):**  
  A “Copy Path” button is available for the `csdtm_dev` folder only. When clicked, it copies the folder path to your clipboard. This path links to an Excel file with detailed checks information split into individual sheets, including subject and data details, which you can open directly from the folder.

---
## 4. How Your Selections and Data are Managed

- **Session-Based Selections:**  
  As you progress through choosing protocols, projects, tasks, and versions, your selections are stored for the duration of your session. This means when you navigate between pages, your choices remain intact.

- **Live Data from the Database:**  
  The application fetches quality check data from SQL database which refreshes every morning. Every time a new page loads, you see the most current data without any global caching that might delay updates.

---

## 4. Support & Additional Information

- **Getting Help:**  
  If you wish to add new checks in the feature, please use the “Submit Query” function to submit the details of checks.

- **Contacting Support:**  
  For further assistance, contact your system administrator or the designated support team listed in your organization’s internal documentation.

- **Additional Resources:**  
  This guide is available within the app through the User Guide popup, and additional technical documentation or training may be provided by the administrators if needed.

---

*This guide is intended for end-users of the cSDTM Quality Checks application. For technical details about the system’s implementation or for troubleshooting development issues, please refer to the developer documentation.*