# Travel360° - Global Travel Advisory Partner

**Travel360°** is a service-oriented client-server web application designed to aggregate real-time country metadata and COVID-19 statistics into a single, unified dashboard. The system demonstrates a modern Service-Oriented Architecture (SOA) by consuming multiple public APIs, securing user access via OAuth 2.0, and persisting aggregated data in a MongoDB database.

## Features

* **Data Aggregation:** Fetches and combines data from *RestCountries API* (Demographics) and *disease.sh* (Health/COVID-19 stats).
* **User Authentication:** Secure login using **Google OAuth 2.0**.
* **Application Security:** dedicated Admin/Service API endpoint protected by a custom **API Key**.
* **Persistent Storage:** Saves aggregated travel records to a **MongoDB** database.
* **Interactive Dashboard:** User-friendly interface to search for countries and view real-time stats.
* **History Tracking:** Users can view their previously saved search records.

## Tech Stack

* **Frontend:** HTML5, CSS3, JavaScript (AJAX), Jinja2 Templates
* **Backend:** Python 3.x, Flask (Microframework)
* **Database:** MongoDB (NoSQL)
* **External APIs:**
    * [RestCountries API](https://restcountries.com/)
    * [Disease.sh API](https://disease.sh/)

## Prerequisites

Before you begin, ensure you have the following installed on your local machine:

1.  **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
2.  **MongoDB Community Server**: [Download MongoDB](https://www.mongodb.com/try/download/community)
3.  **Git**: [Download Git](https://git-scm.com/downloads)
