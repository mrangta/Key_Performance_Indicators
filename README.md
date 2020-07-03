# Key Performance Indicators
### https://security-kpi-dashboard.herokuapp.com/
#### https://mrangta.github.io/Key_Performance_Indicators/

KPIs are designed using Plotly's Dash analytics application framework.

I am reading the dummy data from a csv which contain various security related issues. Csv contains the Issue Id, Issue Title, Issue creation date, Issue closed date, Severity Level, State and Assignee Name. Some of the issues have been resolved and marked as "closed" and some are still open and marked as "open". Every issue has a severity level (i.e Critical,Blocker, Major, Medium, Minor) and some issues don´t have the severity assigned to them and marked as "Not assigned". Each severity needs to be resolved with in a target as stated in below table .  

|  Severity 	| KPI Target |   
|---	        |---	       |
|  Critical 	|  14 days 	 | 
|  Blocker 	  |  14 days   |
|  Major 	    |  14 days   |
|  Medium 	  |  90 days 	 | 
|  Minor 	    |  365 days  |

Below Image shows the various graphs generated from the csv data and also contains a datatable with filter functionality.

![KPI Dashboard](https://github.com/mrangta/Key_Performance_Indicators/blob/master/KPI_dashboard.png?raw=true)
