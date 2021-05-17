# -*- coding: utf-8 -*-
from datetime import datetime,timedelta
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import time
import pandas as pd
import os

# 每天定时使用程序爬取天天基金各个类型的排行榜数据存成excel文档（一共有72个文档，8个类型的基金，9个类型的排行基准）

class RankList():
    def __init__(self):
    #  重复使用的一些关键词or需自行维护的数据
    #  说明：
    #  keywords---srzdf对应日增长排行，szzf对应周增长，s1yzf对应1月增长，s1n对应1年增长，sqjzf：对应自定义区间涨幅（本代码对应5年增长）
    #  f_types ---tall对应全部基金，tgp对应股票型，thh对应混合型，tzq对应债券型，tqdii对应qdii，tlof对应lof，tfof对应fof
    #  holiday_dict---需要自行维护假期（如未维护，会出现重复数据则需要自己手动删除对应假期期间采集的文件即可）
        self.keywords =['srzdf','szzf','s1yzf','s3yzf','s6yzf','s1nzf','s2nzf','s3nzf','sqjzf']
        self.f_types = ["#tall", "#tgp","#thh","#tzq","#tzs",'#tqdii','#tlof','#tfof']
        self.now = datetime.now()
        self.test_url ='http://fund.eastmoney.com/data/fundranking.html#tgp;c0;r;srzdf;pn50;ddesc;qsd20191123;qed20201123;qdii;zq;gg;gzbd;gzfs;bbzt;sfbb'
        self.holidays = ['20210503','20210504','20210505']
        self.holidays_dict={
                           '20210503':'20210430',
                           '20210504':'20210430',
                           '20210505':'20210430',
                           }
    
    def get_date(self,):
    # 计算区间需要的开始日期和结束日期（本代码区间时长为5年）
        dt1 = self.now
        dt0 = dt1-timedelta(1827)
        date1 = dt1.strftime('%Y%m%d') 
        date0 = dt0.strftime('%Y%m%d')
        return date0,date1
    
    def get_urls_list(self,date0,date1):
    # 得到不同基金类型不同排行标准对应的爬取数据的url
        urls_l = []
        all_0 = 'http://fund.eastmoney.com/data/fundranking.html#tall;c0;r;'
        all_1 = ';pn50;ddesc;'
        all_2 ='qdii;zq;gg;gzbd;gzfs;bbzt;sfbb'
        period = 'qsd{};qed{};'.format(date0,date1)
        all_urls = ["{}{}{}{}{}".format(all_0,key,all_1,period,all_2) for key in self.keywords]
        urls_l+=all_urls
        for i in range(1,len(self.f_types)):
            temp_urls = [url.replace("#tall", self.f_types[i], 1) for url in all_urls ]
            urls_l+=temp_urls
        return urls_l
    
    def get_table_content(self,url,xpath='//*[@id="dbtable"]'):
    #  爬取对应url能采集的数据内容
        chrome_opt = Options()  
        chrome_opt.add_argument('--headless') 
        chrome_opt.add_argument('--disable-gpu') 
        chrome_opt.add_argument('--window-size=1366,768')  
        chrome_opt.add_argument("--no-sandbox") 
        driver = webdriver.Chrome("/usr/local/share/chromedriver",options=chrome_opt)
        driver.get(url)
        data = []
        print('-----------------start-----------------')
        time.sleep(10)
        content = driver.find_element_by_xpath(xpath).text
        print('-----------------end-----------------')
        driver.quit()
        return content

    def get_dataframe(self,content):
    #  对爬取的数据内容进行数据整理清洗
        col=['基金代码','基金简称','日期', '单位净值', '累计净值', 'srzdf', 'szzf', 's1yzf',
             's3yzf', 's6yzf', 's1nzf','s2nzf', 's3nzf','今年来','成立来','sqjzf','手续费']
        text_l = content.split('\n')
        data = []
        for i in range(2,len(text_l)):
            temp = []
            if text_l[i].count(' ')==14:
                temp.append(text_l[i-2])
                temp.append(text_l[i-1])
                temp += text_l[i].split(' ')
                data.append(temp)
        df = pd.DataFrame(data=data,columns=col)
        return df
    
    def get_dir_date(self,dt):
    #  得到爬取数据时前一个工作日的日期
        week_day = dt.weekday()
        if week_day>0 and week_day<=5:
            dt1 = dt-timedelta(1)
        elif week_day==0:
            dt1 = dt-timedelta(3)
        else:
            dt1 = dt -timedelta(2)
        dir_date = dt1.strftime('%Y%m%d')
        if dir_date in self.holidays_dict:
            dir_date=self.holidays_dict[dir_date]
        return dir_date
    
    def make_dirs(self,f1_path='../save_information/top50_rank_list'):
    #  按前一个工作日的日期创建存储的文件夹
        dir_date = self.get_dir_date(self.now)
        y = dir_date[:4]
        m = dir_date[4:6]
        d = dir_date[6:]
        f_path = "{}/{}/{}/{}".format(f1_path,y,m,d)
        flag = os.path.exists(f_path)
        if not flag:
            os.makedirs(f_path)
            print(f_path, 'haven been maked!!!')
        else:
            print(f_path, 'haven been existed!!!')
        return flag,f_path
    
    
    def get_excel_path(self,f_path,url):
    #  得到所有excel文件的存储路径
        date = "".join(f_path.split('/')[2:])
        f_type = url.split('#')[1].split(';')[0]
        r_type = url.split('r;')[1].split(';')[0]
        e_path = "{}/{}_{}_{}.xlsx".format(f_path,f_type,r_type,date)
        flag = os.path.exists(e_path)
        return flag,e_path
    
         
    def save_excel(self,f_path,url,xpath='//*[@id="dbtable"]'):
    #  将单个url得到的excel文档进行存储
        flag1,e_path = self.get_excel_path(f_path,url)   
        if not flag1:
            content = self.get_table_content(url,xpath)
            df = self.get_dataframe(content)
            df.to_excel(e_path,index=None)
        flag = os.path.exists(e_path)
        return flag,e_path
    
    def process(self,):
    # 整个采集的流程
        date0,date1 =self.get_date()
        urls = self.get_urls_list(date0,date1)
        flag1,f_path = self.make_dirs()
        error_urls = []
        if not flag1: 
            flag =1
        elif len(os.listdir(f_path))<72:
            flag =1
        else:
            flag = 0
            print('files have been loaded')
        if flag:
            for url in urls:
                flag2,e_path = self.save_excel(f_path,url)
                print(e_path)
                if flag2:
                    print("That {} have been loaded !!!".format(e_path))
                else:
                    print("That {} have not been loaded !!!!!!!".format(e_path))
                    error_urls.append(url)
        return error_urls
        
if __name__=='__main__':
    a = RankList()
    error_urls = a.process()
