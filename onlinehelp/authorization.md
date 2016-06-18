## Auth types
* With auth type "None" all areas are unrestricted.
* With auth type "Form" the basic page is loaded and login is done via a form. A token is stored in your browser so you don't have to login again for 14 days. 
* With auth type "Basic" you login via basic HTTP authentication. With all areas restricted this is the most secure as nearly no data is loaded from the server before you auth.

### Note
You need to make sure that you don't restrict access to the admin area and have no user without access to that area.