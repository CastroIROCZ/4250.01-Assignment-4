from pymongo import MongoClient
import bs4
from bs4 import BeautifulSoup

#Function to print debug messages
def debug_print(message):
    print(f"[DEBUG] {message}")

#Connect to the MongoDB client
client = MongoClient('localhost', 27017)
debug_print("Connected to MongoDB.")

#Define the database and collection
db = client['cs_crawler']
pages_collection = db['pages']
professors_collection = db['professors']
debug_print("Database and collection selected.")

#Fetch the Permanent Faculty page HTML from MongoDB
faculty_page_url = 'https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml'
faculty_page = pages_collection.find_one({'url': faculty_page_url})
debug_print(f"Searching for URL in database: {faculty_page_url}")

#Parse the HTML content if the page was found
if faculty_page:
    html_content = faculty_page['html'].decode('utf-8')
    soup = BeautifulSoup(html_content, 'html.parser')
    debug_print("Permanent Faculty page HTML content retrieved.")

    #Find the container with all faculty members
    faculty_containers = soup.select('div.clearfix')
    debug_print(f"Found {len(faculty_containers)} faculty member containers.")

    #Process each faculty member container
    for container in faculty_containers:
        h2_element = container.find('h2')
        if h2_element:
            name = h2_element.get_text(strip=True)
        else:
            debug_print("No h2 element found in this container.")
            continue

        title = office = phone = email = web = ""

        #Extract all the <p> elements that contain the information
        p_element = container.find('p')
        if p_element:
            strong_tags = p_element.find_all('strong')
            for strong_tag in strong_tags:
                category = strong_tag.get_text(strip=True).lower()
                info = strong_tag.next_sibling
                if info and isinstance(info, str):
                    info = info.strip().lstrip(':').strip()  #Strip leading colons and whitespace

                if 'title:' in category or 'title' in category: #an or statment is needed due to inconsistent formatting
                    title = info
                elif 'office:' in category or 'office' in category:
                    office = info
                elif 'phone:' in category or 'phone' in category:
                    phone = info
                elif 'email:' in category or 'email' in category:
                    email_tag = strong_tag.find_next_sibling('a')
                    if email_tag and email_tag.has_attr('href'):
                        email = email_tag['href'].replace('mailto:', '')
                elif 'web:' in category or 'web' in category:
                    web_tag = strong_tag.find_next_sibling('a')
                    if web_tag and web_tag.has_attr('href'):
                        web = web_tag['href']

        faculty_member = {
            'name': name,
            'title': title,
            'office': office,
            'phone': phone,
            'email': email,
            'web': web
        }

        #Insert into MongoDB
        professors_collection.insert_one(faculty_member)
        debug_print(f"Inserted faculty member: {name}")

    debug_print("Faculty data insertion complete.")
else:
    debug_print("Permanent Faculty page not found in the database.")

#Close the MongoDB client connection
client.close()
debug_print("MongoDB connection closed.")
