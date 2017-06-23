import urllib.request as urllib2
from bs4 import BeautifulSoup
import sys
import requests
from bs4 import BeautifulSoup as soup
import operator
import os

""""

These list of functions consist of the logic and methodology behind the ranking

Constants
    common_encodings  - list of encodings for Payscale for URL
    fairy_god_boss_encodings - list of encodings for FGB URL

Functions
    get_ranking_for_company
    clamp_salary
    clamp_percent
    alculate_ranking
    get_salary_and_percentage
    get_benefits

"""

common_encodings = { "hm": "H%26M_Hennes_%26_Mauritz_Inc.", "forever21":"Forever_21%2c_Inc.", "facebook" : "Facebook_Inc", "gm":"general-motors"}

fairy_god_boss_encodings = { "hm" : "h-m", "forever21": "forever-21"}


def get_ranking_for_company(company_name):

    # This is the entrypoint function
    # Parameters 
    # Company name - [string]
    # Output
    # Ranking [integer] 
    # Percentage of women [integer]
    # Benefits (weeks of maternity leave) [integer]
    # Salary difference (raw) [integer] 
    # Breakdown (what a man makes for every dollar a woman makes) [integer]

    (salary, breakdown, p_women)= get_salary_and_percentage(company_name)
    benefits = get_benefits(company_name)
    ranking = calculate_ranking(salary, p_women, benefits)
    return  ranking,  p_women,  benefits, salary, breakdown


def clamp_salary(number):
    return max(min(number, 30000), 0)

def clamp_percent(number):
    return max(min(number, 50), 10)

def fetch_url(address):
    # Parameters 
    # Address -  http address to fetch [string]
    # Output
    # JSON page
    request = urllib2.Request(address, None, {'User-Agent':'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)'} )
    urlfile = urllib2.urlopen(request)
    page = urlfile.read(200000000)
    urlfile.close()
    return page

def calculate_ranking(salary, percent, benefit):
    #  Parameters
    #  Salary - the pay gap [integer] 
    #  Percentage - percent of women in the workplace [integer]. 
    #  Benefit - number of weeks paid maternity leave [integer] 
    #  Output
    #  Rankings [integer]
    national_avg = 0
    res = 0
    total = 1
    if salary is not None:
        salary_diff = clamp_salary(-1*salary)
        normalized = float(salary_diff - (-1*30000))/30000.0
        res += normalized
        total += 1
    if percent is not None:
        percent_clamp = clamp_percent(percent)
        normalized = float(percent_clamp - 10)/40.0
        total += 1
        res += normalized
    if (benefit is not None):
        try:
            int(benefit)
            res +=  0.01*(float(str(benefit))- float(national_avg))
            total += 1
        except:
            pass
    return res/total

def get_salary_and_percentage(company_name):

    #  This function queries and parses Payscale data. 
    #  Parameters
    #  Company_name [string]
    #  Output
    #  Average salary - average pay gap [integer]
    #  Brekadown salary - the number of dollars a man makes for $1 a woman makes [ifloat] 
    #. Percentage of women [float]

    breakdown_salary = None
    diff_average_salary = None
    if (common_encodings.get(company_name) is not None):
        company_name = common_encodings[company_name]
    address =  "http://www.payscale.com/research/US/Employer=%s/Salary#by_Gender" % company_name
    select = 0
    try:
        page = fetch_url(address)
        soup_url = soup(page, 'lxml')
        diff_average_salary = None
        percent_women = None

        all_divs = soup_url.find_all("div", class_="text-center")
    except:
        try:
            address_prelim = "http://www.payscale.com/rcsearch.aspx?category=&str=%s&CountryName=United+States&SourceId=" % company_name
            page = fetch_url(address_prelim)
            soup_url = soup(page, 'lxml')
            tag = soup_url.find_all("h2", class_="RCSearchTitle")
            tag = tag[len(tag) - 1]
            all_lis = tag.find_all_next('li')
            if (len(all_lis) == 0):
                return None, None, None
            else:
                curr = all_lis[0]
                curr = str(curr).split("Employer=")
                curr = curr[1]
                company = curr.split("/Salary")[0]
                address =  "http://www.payscale.com/research/US/Employer=%s/Salary#by_Gender" % company_name
                page = fetch_url(address)
                soup_url = soup(page, 'lxml')
                diff_average_salary = None
                percent_women = None

                all_divs = soup_url.find_all("div", class_="text-center")
        except:
            return None, None, None

    try:
        for i in all_divs:
            if  (select == 0) and ("Female" in i.text):
                 percent_women = i.text.split('<br/>')[0]
                 percent_women  = percent_women.split("\n")[2]
                 percent_women = percent_women.split('%')[0]
                 percent_women = int(percent_women)
                 select += 1
        all_td = soup_url.find_all("td", class_="text-center")

        index = 0
    except:
        pass

    try:
        for j in all_td:
            if  (index == 0) and ("Salary" in j.text):
                if ("-" in j.text):
                     salary_women = str(j.text).split('Salary')[1]
                     salary_women = salary_women.split("-")
                     salary_women[0] = str(salary_women[0]).replace("$", "")
                     salary_women[0] = str(salary_women[0]).replace(" ", "")
                     salary_women[0] = str(salary_women[0]).replace(",", "")
                     salary_women[1] = str(salary_women[1]).replace("$", "")
                     salary_women[1] = str(salary_women[1]).replace(" ", "")
                     salary_women[1] = str(salary_women[1]).replace(",", "")
                index += 1
            elif  (index == 1) and ("Salary" in j.text):
                 salary_men = j.text.split('<br/>')[0]
                 salary_men  = salary_men.split("\n")[2]
                 salary_men = salary_men.split('%')[0]
                 if "-" in salary_men:
                     salary_men = salary_men.split("-")
                     salary_men[0] = str(salary_men[0]).replace("$", "")
                     salary_men[0] = str(salary_men[0]).replace(" ", "")
                     salary_men[0] = str(salary_men[0]).replace(",", "")
                     salary_men[1] = str(salary_men[1]).replace("$", "")
                     salary_men[1] = str(salary_men[1]).replace(" ", "")
                     salary_men[1] = str(salary_men[1]).replace(",", "")
                 index += 1

        diff_lower = float((int(salary_men[0]) - int(salary_women[0])))/ float(salary_men[0])
        diff_higher = float((int(salary_men[1]) - int(salary_women[1])))/ float(salary_men[1])
        diff_average_salary = (diff_lower + diff_higher)/2
        breakdown_salary =  float("{0:.3f}".format(diff_average_salary))
        breakdown_salary *= 10
    except:
        pass
    return diff_average_salary, breakdown_salary, percent_women


def get_benefits(company_name):

    #  This function queries and parses FairyGodBoss.
    #  Parameters
    #  Company_name [string]
    #  Output
    #  Benefits [integer]

    if fairy_god_boss_encodings.get(company_name) is not None:
        company_name = fairy_god_boss_encodings[company_name]

    try:
        address_two = "https://fairygodboss.com/companies/benefits/%s" % company_name
        page_two = fetch_url(address_two)
    except:
        return None
    soup_u = soup(page_two, 'lxml')
    s = 0
    maternity_benefit = None
    try:
        for k in soup_u.find_all("div", class_="benTopRight"):
            if (s == 2):
                maternity_benefit = k.text.split("Median")[0]
                maternity_benefit = maternity_benefit.split("start")
                maternity_benefit = maternity_benefit[0].split('Median')[0]
                maternity_benefit = maternity_benefit.split("  ")
                maternity_benefit = maternity_benefit[len(maternity_benefit) -1]
                if "tip" not in maternity_benefit:
                    maternity_benefit = int(maternity_benefit)
            s += 1
    except:
        print("Unexpected error:", sys.exc_info()[0])
    return maternity_benefit

