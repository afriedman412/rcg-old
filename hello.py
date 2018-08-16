#!/usr/bin/env python

# Import modules for CGI handling 
import cgi, cgitb 

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
name = form.getvalue('name')

print("Content-type:text/html\r\n\r\n")
print("<html>")
print("<head>")
print("<title>what it do</title>")
print("</head>")
print("<body>")
print("<h2> it's %s im the peoples champ</h2>" % name)
print("</body>")
print("</html>")