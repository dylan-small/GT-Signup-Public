from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from twilio.rest import Client
#Parses user info (username, password, phone)
def parseUserInfo(filename):
	with open(filename) as file:
		contents = file.readlines()
		return contents
#parses class info (class, teacher, etc)
def parseClassInfo(filename):
	contents = list()
	with open(filename) as file:
		for line in file:
			content = line.rstrip('\n').split(', ')
			content.insert(0,False)
			print(content)
			contents.append(content)
	return contents
#Sends user a text message
def sendText(NAME,CRN,REM,PHONE):
	acc_SID = 'INPUT_ACC_SID_HERE'
	acc_TOKEN = 'INPUT_ACC_TOKEN_HERE'
	client = Client(acc_SID,acc_TOKEN)
	client.messages.create(
		to = PHONE,
		from_ = '+1 INPUT_ACC_PHONE_NUMBER_HERE',
		body = str(NAME)+ ' : ' + str(CRN) + ' : ' + str(REM)
	)
def isFullSearch(content,index):
	return len(content[index]) > 3
#init browser and contents of .keys files
options = Options()
#options.add_argument('--headless')
driver = webdriver.Chrome(chrome_options=options)
print('initialized browser...')
userinfo = parseUserInfo('userinfo.keys')
classinfo = parseClassInfo('classinfo.keys')

#navigate to buzzport
driver.get('https://login.gatech.edu/cas/login?service=http%3A%2F%2Fbuzzport.gatech.edu%2Fsso%3Bjsessionid%3D903D4B8E9BD95A404A429A888776F357')
driver.find_element_by_xpath('//*[@id="username"]').send_keys(userinfo[0])
driver.find_element_by_xpath('//*[@id="password"]').send_keys(userinfo[1])

#wait for buzzport to load, then go to the student page
while True:
	try:
		driver.find_element_by_xpath('//*[@id="u3651l1s13"]').click()
		print('student website loading...')
		break
	except Exception:
		print('buzzport hasn\'t loaded yet.. please wait')
print('student website loaded!')

#navigate to OSCAR
while True:
	try:
		driver.find_element_by_xpath('//*[@id="u3651l1n31"]/div[2]/table/tbody/tr[1]/td[1]/div/a').click()
		print('oscar website loading...')
		break
	except Exception:
		print('OSCAR website not loaded yet... please wait')
print('oscar website loaded!')

#enter a loop to check for all classes
registered = False
found = False
while not registered:
	for index,course in enumerate(classinfo):
		if(not classinfo[index][0]):
			driver.get('https://oscar.gatech.edu/pls/bprod/bwskfreg.P_AltPin')
			driver.find_element_by_xpath('/html/body/div[3]/form/input').click()
			driver.find_element_by_xpath('/html/body/div[3]/form/input[20]').click()
			print('registration website loaded')

			#navigate to each course
			subject_and_number = classinfo[index][1].split(' ')
			#select subject
			select_element = driver.find_element_by_xpath('//*[@id="subj_id"]')
			options = select_element.find_elements_by_tag_name('option')
			for option in options:
				if(option.get_attribute('value') == subject_and_number[0]):
					option.click()
					print('selected:',option.get_attribute('value'))
					driver.find_element_by_xpath('/html/body/div[3]/form/input[108]').click()
					break
			#select number
			select_element = driver.find_element_by_xpath('/html/body/div[3]/table[2]/tbody')
			trs = select_element.find_elements_by_tag_name('tr')
			for tr in trs:
				tds = tr.find_elements_by_tag_name('td')
				for td in tds:
					if(td.text == str(subject_and_number[1])):
						print('selected:',td.text)
						select_element = tds[2]
						form = select_element.find_elements_by_tag_name('form')
						for f in form:
							select_element = f
							ins = select_element.find_elements_by_tag_name('input')
							for i in ins:
								if(i.get_attribute('value') == 'View Sections'):
									i.click()
									break
						found = True
						break
				if(found):
					found = False
					break
			#analyze class information (teacher,time,section,etc) then check to see if some are remaining
			select_element = driver.find_element_by_xpath('/html/body/div[3]/form/table/tbodya')
			trs = select_element.find_elements_by_tag_name('tr')
			for tr in trs:
				tds = tr.find_elements_by_tag_name('td')
				i = 0
				for td in tds:
					if(isFullSearch(classinfo,index)):
						if(classinfo[index][2] in td.text and classinfo[index][3] in tds[i-7].text):
							print('analyzing',td.text,tds[i-7].text,'...')
							CRN = tds[i-16].text
							REM = tds[i-4].text
							print(td.text,CRN,REM,tds[i-7].text)
							if(int(REM) > 0):
								name = tds[i-14].text + ' ' + tds[i-15].text
								sendText(name,CRN,REM,userinfo[2])
								classinfo[index][0] = True
								found = True
								break
							else:
								print('no openings found for teacher',td.text,'at',tds[i-7].text)
					else:
						if(td.text == classinfo[index][2]):
							print('analyzing',td.text,'...')
							CRN = tds[i-3].text
							REM = tds[i+9].text
							print(td.text,CRN,REM)
							if(int(REM) > 0):
								name = tds[i-1].text + ' ' + tds[i-2].text
								sendText(name,CRN,REM,userinfo[2])
								classinfo[index][0] = True
								found = True
								break
							else:
								print('no openings for',td.text)
					i += 1