from kivy.app import App
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import ObjectProperty
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.properties import StringProperty


import urllib2
import urllib
import re
from cookielib import CookieJar
from BeautifulSoup import BeautifulSoup

class PortalAccess(object):

    def __init__(self):
        self.home_url = 'https://pamet-sapphire.k12system.com/CommunityWebPortal/Welcome.cfm'
        self.backpack_url = 'https://pamet-sapphire.k12system.com/CommunityWebPortal/Backpack/StudentHome.cfm?STUDENT_RID={id}'
        self.student_courses_url = 'https://pamet-sapphire.k12system.com/CommunityWebPortal/Backpack/StudentClasses.cfm?STUDENT_RID={id}'
        self.course_url = 'https://pamet-sapphire.k12system.com/CommunityWebPortal/Backpack/StudentClassPage.cfm?STUDENT_RID={id}&COURSE_SECTION_GUID={section_id}'
        self.grade_url = 'https://pamet-sapphire.k12system.com/CommunityWebPortal/Backpack/StudentClassGrades.cfm?STUDENT_RID={id}&COURSE_SECTION_GUID={section_id}&MP_CODE={MPNUM}'
        
        self.cj = CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        
    def open_home(self):
        self.response = self.opener.open(self.home_url, self.data)
    def open_backpack(self, id):
        self.response = self.opener.open(self.backpack_url.format(id=id))
    def open_detailed_grades(self, id, course_id, mp_number):
        self.response = self.opener.open(self.grade_url.format(id=id, section_id=course_id, MPNUM=mp_number))
    def open_course(self, id, course_id):
        self.response = self.opener.open(self.course_url.format(id=id, section_id=course_id))
    def open_course_list(self, id):
        self.response = self.opener.open(self.student_courses_url.format(id=id))
        
    def get_current_html(self):
        if self.response:
            return self.response.read()
        else:
            pass
        
    def is_student_account(self):
        self.open_home()
        html = self.get_current_html()
        reg = re.search('MY STUDENTS \((\d)\)', html)
        if reg:
            return False
        else:
            return True
         
    def get_number_of_students(self):
        self.open_home()
        html = self.get_current_html()
        reg = re.search('MY STUDENTS \((\d)\)', html)
        return reg.group(1)
        
    def get_student_ids(self):
        #Gets ids from welcome page
        self.open_home()
        html = self.get_current_html()
        soup = BeautifulSoup(html)
        ids = dict()
        for link in soup.findAll('a'):
            reg = re.search('/Backpack\/StudentHome\.cfm\?STUDENT_RID=(\d+)', str(link))
            if reg:
                ids[str(link.contents[-1])] = reg.group(1)
            else:
                pass
        return ids

        
    def get_course_list(self, id):
        self.open_course_list(id)
        html = self.get_current_html()
        soup = BeautifulSoup(html)
        ids = dict()
        for link in soup.findAll('a'):
            reg = re.search(r'\/Backpack\/StudentClassPage\.cfm\?STUDENT_RID={id}&amp;COURSE_SECTION_GUID=([0-9-A-Z]+)'.format(id=id), str(link))
            if reg:
                ids[str(link.contents[-1])] = reg.group(1)
            else:
                pass
        return ids
        
    def set_active_id(self, id):
        self.active_id = id
        
    def refresh(self):
        self.student_ids = self.get_student_ids()
        self.course_ids = self.get_course_list(self.active_id)

        
    def get_course_grades(self, id, course_id):
        self.open_course(id, course_id)
        html = self.get_current_html()
        soup = BeautifulSoup(html)
        table = soup.find("table", attrs={"class":"classGradesTbl"})
        
        grades = dict()
        count = 0       
        if not table:
            r = dict()
            r['YTD'] = ''
            return r
            
        for x in table.findAll('td'):
            count = count + 1
            grade = x.find('a')
            if grade:
                num = grade.contents[-1].strip()
                grades['MP'+str(count)] = str(num)
            else:
                other_grade = str(x.contents[-5])
                other_grade_name = str(x.find('b').contents[-1])
                grades[other_grade_name.strip()] = other_grade.strip()
                
        if 'YTD' not in grades:
            grades['YTD'] = ''
        return grades

        
    def get_detailed_grades(self, id, course_id, mp_number):
        #Returns list with dicts. with number as list and info as dict. dict has name, score, total_score, date, category
        self.open_detailed_grades(id, course_id, mp_number)
        html = self.get_current_html()
        soup = BeautifulSoup(html)
        table = soup.find("table", attrs={"id":"assignments"})
        trs = table.findAll('tr')
        
        assignments = []
        for tr in range(len(trs)):
            #first tr is title
            if tr == 0:
                continue

            tds = trs[tr].findAll('td')

            info = dict()
            info['name'] = tds[0].contents[-1]
            info['score'] = tds[1].contents[-1]
            info['total_score'] = tds[2].contents[-1]
            info['date'] = tds[3].contents[-1]
            info['category'] = tds[4].contents[-1]
            
            assignments.append(info)
        return assignments
        
    #def get_detailed_grades_categories(self, id, course_id, mp_number):
    #    self.open_detailed_grades(id, course_id, mp_number)
    #    html = self.get_current_html()
    #    soup = BeautifulSoup(html)
    #    table = soup.find("table", attrs={"id":"assignmentCategories"})
    #    trs = table.findAll('tr')
    #    
    #    assignments = []
    #    for tr in range(len(trs)):
    #        tds = trs[tr].findAll('td')
    #        info = dict()
    #        info['name'] = tds[0].contents[-1]            
    #        assignments.append(info)
    #    return assignments
        
    def login(self, username, password, pin):
        # Prepare the data
        self.query_args = { 'j_username':username, 'j_password':password, 'j_pin':pin }

        # This urlencodes your data (that's why we need to import urllib at the top)
        self.data = urllib.urlencode(self.query_args)

        # Send HTTP POST request
        self.opener.open(self.home_url)
        self.response = self.opener.open(self.home_url, self.data)
        self.student_account = self.is_student_account()
        
        if self.student_account is False:
            self.student_number = self.get_number_of_students()
        else:
            self.student_number = None
            
        self.student_ids = self.get_student_ids()
        self.active_id = self.student_ids[self.student_ids.keys()[0]]
        self.course_ids = self.get_course_list(self.active_id)


class AccountDetailsForm(AnchorLayout):
    pin_box = ObjectProperty()
    username_box = ObjectProperty()
    password_box = ObjectProperty()

    def login(self):
        username = self.username_box.text
        pin = self.pin_box.text
        password = self.password_box.text
 
        app = Portal.get_running_app()
        app.portal_login(username, password, pin)
        
        app.root.show_course_list()
        
class CourseListItem(BoxLayout):
    text = StringProperty()
    grades = StringProperty()
    background = ObjectProperty()
        
class CourseList(BoxLayout):
    list_view = ObjectProperty()
 
    def __init__(self):
        super(CourseList, self).__init__()
        self.app = Portal.get_running_app()
        self.list_view.adapter.data = sorted(self.app.pa.course_ids.keys())
        
    def grade_converter(self, index, course_name):
        app = Portal.get_running_app()
        ytd = app.get_grades(course_name)
        
        result = {
            "text": course_name,
            "grades": 'YTD: ' + ytd
        }
        
        if index % 2:
            result['background'] = (0, 0, 0, 1)
        else:
            result['background'] = (0.05, 0.05, 0.07, 1)
     
        return result
        
class PortalRoot(BoxLayout):
    def show_course_list(self):
        self.clear_widgets()
        self.course_list = CourseList()
        self.add_widget(self.course_list)

class Portal(App):
        
    def portal_login(self, username, password, pin):
        self.pa = PortalAccess()
        self.pa.login(username, password, pin)
        self.pa.set_active_id(self.pa.student_ids['Achyut Reddy'])
        self.pa.refresh()
        print self.pa.course_ids
        
    def get_grades(self, course_name):
        print course_name
        return self.pa.get_course_grades(self.pa.active_id, self.pa.course_ids[course_name])['YTD']
        
        
Portal().run()