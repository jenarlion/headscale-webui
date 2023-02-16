import os, headscale, requests
from flask    import Flask

app = Flask(__name__)

def pretty_print_duration(duration):
    days, seconds = duration.days, duration.seconds
    hours = (days * 24 + seconds // 3600)
    mins  = ((seconds % 3600) // 60)
    secs  = (seconds % 60)
    if   days  > 0: return str(days ) + " days ago"     if days  >  1 else str(days ) + " day ago"
    elif hours > 0: return str(hours) + " hours ago"    if hours >  1 else str(hours) + " hour ago"
    elif mins  > 0: return str(mins ) + " minutes ago"  if mins  >  1 else str(mins ) + " minute ago"
    else:           return str(secs ) + " seconds ago"  if secs  >= 1 or secs == 0 else str(secs ) + " second ago"

def text_color_duration(duration):
    days, seconds = duration.days, duration.seconds
    hours = (days * 24 + seconds // 3600)
    mins  = ((seconds % 3600) // 60)
    secs  = (seconds % 60)
    if   days  > 30: return "grey-text                      "
    elif days  > 14: return "red-text         text-darken-2 "
    elif days  >  5: return "deep-orange-text text-lighten-1"
    elif days  >  1: return "deep-orange-text text-lighten-1"
    elif hours > 12: return "orange-text                    "
    elif hours >  1: return "orange-text      text-lighten-2"      
    elif hours == 1: return "yellow-text                    "
    elif mins  > 15: return "yellow-text      text-lighten-2"
    elif mins  >  5: return "green-text       text-lighten-3"
    elif secs  > 30: return "green-text       text-lighten-2" 
    else:            return "green-text                     "

def key_check():
    api_key    = headscale.get_api_key()
    url        = headscale.get_url()

    # Test the API key.  If the test fails, return a failure.  
    # AKA, if headscale returns Unauthorized, fail:
    status = headscale.test_api_key(url, api_key)
    if status != 200: return False
    else:
        # Check if the key needs to be renewed
        headscale.renew_api_key(url, api_key) 
        return True

def get_color(id, type = ""):
    # Define the colors... Seems like a good number to start with
    if type == "text":
        colors = [
            "red-text         text-lighten-1",
            "teal-text        text-lighten-1",
            "blue-text        text-lighten-1",
            "blue-grey-text   text-lighten-1",
            "indigo-text      text-lighten-2",
            "green-text       text-lighten-1",
            "deep-orange-text text-lighten-1",
            "yellow-text      text-lighten-2",
            "purple-text      text-lighten-2",
            "indigo-text      text-lighten-2",
            "brown-text       text-lighten-1",
            "grey-text        text-lighten-1",
        ]
        index = id % len(colors)
        return colors[index]
    else:
        colors = [
            "red         lighten-1",
            "teal        lighten-1",
            "blue        lighten-1",
            "blue-grey   lighten-1",
            "indigo      lighten-2",
            "green       lighten-1",
            "deep-orange lighten-1",
            "yellow      lighten-2",
            "purple      lighten-2",
            "indigo      lighten-2",
            "brown       lighten-1",
            "grey        lighten-1",
        ]
        index = id % len(colors)
        return colors[index]

def format_error_message(type, title, message):
    content = """
        <ul class="collection">
        <li class="collection-item avatar">
    """
    
    match type.lower():
        case "warning":
            icon  = """<i class="material-icons circle yellow">priority_high</i>"""
            title = """<span class="title">Warning - """+title+"""</span>"""
        case "success":
            icon  = """<i class="material-icons circle green">check</i>"""
            title = """<span class="title">Success - """+title+"""</span>"""
        case "error":
            icon  = """<i class="material-icons circle red">warning</i>"""
            title = """<span class="title">Error - """+title+"""</span>"""
        case "information":
            icon  = """<i class="material-icons circle grey">help</i>"""
            title = """<span class="title">Information - """+title+"""</span>"""

    content = content+icon+title+message        
    content = content+"""
            </li>
        </ul>
    """

    return content

def access_checks():
    url = headscale.get_url()

    # Return an error message if things fail. 
    # Return a formatted error message for EACH fail.
    checks_passed   = True # Default to true.  Set to false when any checks fail.
    data_readable   = False # Checks R permissions of /data
    data_writable   = False # Checks W permissions of /data
    data_executable = False # Execute on directories allows file access, even if you cannot list the directory contents
    file_readable   = False # Checks R permissions of /data/key.txt
    file_writable   = False # Checks W permissions of /data/key.txt
    file_exists     = False # Checks if /data/key.txt exists
    config_readable = False # Checks if the headscale configuration file is readable


    # Check 1: Check: the Headscale server is reachable:
    server_reachable = False
    response = requests.get(str(url)+"/health")
    if response.status_code == 200:
        server_reachable = True
    else: 
        checks_passed = False
        app.logger.error("Headscale URL: Response 200: FAILED")

    # Check: /data is rwx for 1000:1000:
    if os.access('/data/', os.R_OK):  data_readable = True
    else:
        app.logger.error("/data READ: FAILED")
        checks_passed = False
    if os.access('/data/', os.W_OK):  data_writable = True
    else:
        app.logger.error("/data WRITE: FAILED")
        checks_passed = False
    if os.access('/data/', os.X_OK):   data_executable = True
    else:
        app.logger.error("/data EXEC: FAILED")
        checks_passed = False

    # Check: /data/key.txt exists and is rw:
    if os.access('/data/key.txt', os.F_OK): 
        file_exists = True
        if os.access('/data/key.txt', os.R_OK): file_readable = True
        else:
            app.logger.error("/data/key.txt READ: FAILED")
            checks_passed = False
        if os.access('/data/key.txt', os.W_OK):  file_writable = True
        else:
            app.logger.error("/data/key.txt WRITE: FAILED")
            checks_passed = False
    else: app.logger.error("/data/key.txt EXIST: FAILED - NO ERROR")

    # Check: /etc/headscale/config.yaml is readable:
    if os.access('/etc/headscale/config.yaml', os.R_OK):  config_readable = True
    elif os.access('/etc/headscale/config.yml', os.R_OK): config_readable = True
    else: 
        app.logger.error("/etc/headscale/config.y(a)ml: READ: FAILED")
        checks_passed = False

    if checks_passed: 
        app.logger.error("All startup checks passed.")
        return "Pass"

    messageHTML = ""
    # Generate the message:
    if not server_reachable:
        app.logger.error("Server is unreachable")
        message = """
        <p>Your headscale server is either unreachable or not properly configured.  
        Please ensure your configuration is correct (Check for 200 status on 
        """+url+"""/api/v1 failed.  Response:  """+str(response.status_code)+""".)</p>
        """

        messageHTML += format_error_message("Error", "Headscale unreachable", message)

    if not config_readable:
        app.logger.error("Headscale configuration is not readable")
        message = """
        <p>/etc/headscale/config.yaml not readable.  Please ensure your 
        headscale configuration file resides in /etc/headscale and 
        is named "config.yaml" or "config.yml"</p>
        """

        messageHTML += format_error_message("Error", "/etc/headscale/config.yaml not readable", message)

    if not data_writable:
        app.logger.error("/data folder is not writable")
        message = """
        <p>/data is not writable.  Please ensure your 
        permissions are correct. /data mount should be writable 
        by UID/GID 1000:1000.</p>
        """

        messageHTML += format_error_message("Error", "/data not writable", message)

    if not data_readable:
        app.logger.error("/data folder is not readable")
        message = """
        <p>/data is not readable.  Please ensure your 
        permissions are correct. /data mount should be readable 
        by UID/GID 1000:1000.</p>
        """

        messageHTML += format_error_message("Error", "/data not readable", message)

    if not data_executable:
        app.logger.error("/data folder is not readable")
        message = """
        <p>/data is not executable.  Please ensure your 
        permissions are correct. /data mount should be readable 
        by UID/GID 1000:1000. (chown 1000:1000 /path/to/data && chmod -R 755 /path/to/data)</p>
        """

        messageHTML += format_error_message("Error", "/data not executable", message)


    if file_exists: # If it doesn't exist, we assume the user hasn't created it yet.  Just redirect to the settings page to enter an API Key
        if not file_writable:
            app.logger.error("/data/key.txt is not writable")
            message = """
            <p>/data/key.txt is not writable.  Please ensure your 
            permissions are correct. /data mount should be writable 
            by UID/GID 1000:1000.</p>
            """

            messageHTML += format_error_message("Error", "/data/key.txt not writable", message)

        if not file_readable:
            app.logger.error("/data/key.txt is not readable")
            message = """
            <p>/data/key.txt is not readable.  Please ensure your 
            permissions are correct. /data mount should be readable 
            by UID/GID 1000:1000.</p>
            """

            messageHTML += format_error_message("Error", "/data/key.txt not readable", message)

    return messageHTML

def load_checks():
    # General error checks.  See the function for more info:
    if access_checsk() == "Pass": return 'error_page'
    # If the API key fails, redirect to the settings page:
    if key_check() == False: return 'settings_page'
    return "Pass"