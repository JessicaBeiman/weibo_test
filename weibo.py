from os import getcwd
from urllib.parse import urlencode
from pyquery import PyQuery as pq
import requests
import pandas as pd
import re
import time
import datetime
import traceback
import random


# 获取全文
def get_longtext(mid: str):
    url = f"https://m.weibo.cn/statuses/extend?id={mid}"
    resp = requests.get(url, timeout=60).json()
    all_text = pq(resp['data']['longTextContent']).text().replace('\n', '.')
    return all_text


# 获取用户发布的微博文字和图片
def get_user_weibo(uid, cookie, page_num):
    base_url = 'https://m.weibo.cn/api/container/getIndex?'
    headers = {
        'Host': 'm.weibo.cn',
        'Referer': f'https://m.weibo.cn/u/{uid}',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'cookie': cookie
    }
    params = {
        'type': 'uid',
        'value': uid,
        'containerid': '107603' + uid,  # 待获取的用户的containerid. “微博”页的containerid='107603'+uid; “超话”页的containerid='231475'+uid;
        'page': page_num
    }
    url = base_url + urlencode(params)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200 & response.json().get('ok') == 1:
            items = response.json().get('data').get('cards')  # items是一个数组list []
            weibo_list = []
            pic_list = []
            for item in items:
                if item.get('card_type') == 9:  # card_type == 9的才是博文，card_type == 11/1不清楚类型
                    item = item.get('mblog')  # item是一个字典dict{}
                    weibo = {}
                    weibo['id'] = item.get('id')  # 微博的id
                    weibo['text'] = item.get('text')  # 微博的文字
                    weibo['comments_count'] = item.get('comments_count')  # 微博的评论数量
                    weibo['attitudes_count'] = item.get('attitudes_count')  # 微博的点赞数量
                    weibo['reposts_count'] = item.get('reposts_count')  # 微博的转发数量
                    weibo['created_at'] = item.get('created_at')  # 微博创建日期
                    weibo['isLongText'] = item.get('isLongText')  # 是否超过140个字符
                    weibo['pic_num'] = item.get('pic_num')  # 图片数量
                    # 如果isLongText=true, 则获取全文
                    if item.get('isLongText'):
                        extend_id = re.findall(r'href="/status/(.+?)"', weibo['text'])[0]
                        weibo['text'] = get_longtext(extend_id)
                    else:
                        weibo['text'] = pq(item.get('text')).text().replace('\n', '.')
                    weibo_list.append(weibo)
                    # 如果图片的数量大于0，则爬取图片url
                    if item.get('pic_num') > 0:
                        for pic in item.get('pics'):
                            pic_url = pic['large']['url']
                            pic_list.append(pic_url)
            return weibo_list, pic_list
    except Exception as e:
        print(traceback.print_exc())


# 保存解析结果到csv文档
def save_result(uid, page_num, result_list):
    csv_path = getcwd() + f'\\{uid}.csv'
    df = pd.DataFrame(result_list)
    if page_num == 1:
        df.to_csv(csv_path, mode='w', index=False, header=True, encoding='utf-8_sig')
    else:
        df.to_csv(csv_path, mode='a', index=False, header=False, encoding='utf-8_sig')


# 保存图片url到txt文档
def save_url(uid, page_num, pic_list):
    if page_num == 1:
        f = open(getcwd() + f'\\{uid}_img.txt', "w", encoding='utf-8')
        url_str = ''
        for url in pic_list:
            url_str = url_str + url + '\n'
        f.write(url_str)
    else:
        f = open(getcwd() + f'\\{uid}_img.txt', "a", encoding='utf-8')
        url_str = ''
        for url in pic_list:
            url_str = url_str + url + '\n'
        f.write(url_str)


# 计算帖子发布的时间与当天0点时间的比较（为了只获取当前发布的帖子）
def compare_time(post_time):
    post_time = time.mktime(time.strptime(post_time, '%a %b %d %X %z %Y'))
    today_time = time.mktime(datetime.date.today().timetuple())
    return int(post_time) - int(today_time)


# 获取单条微博的信息：创建时间
def get_post_time(post_id):
    url = f"https://m.weibo.cn/statuses/show?id={post_id}"
    resp = requests.get(url, timeout=60).json()
    create_time = resp['data']['created_at']
    return create_time


# 获取超话参数
def get_super_topic_id(uid, cookie):
    base_url = 'https://m.weibo.cn/api/container/getIndex?'
    headers = {
            'Host': 'm.weibo.cn',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'cookie': cookie  # param
        }
    params = {
            'type': 'uid',
            'value': uid,
            'containerid': '231475' + uid,  # 待获取的用户的containerid. “微博”页的containerid='107603'+uid; “超话”页的containerid='231475'+uid;
        }
    url = base_url + urlencode(params)
    print(url)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200 and response.json().get('ok') == 1:
            super_topic_id = response.json().get('data').get('cardlistInfo').get('hide_oids')[0].split(':')[1]
            print('super_topic_id: ', super_topic_id)
            return super_topic_id
    except Exception as e:
        print(traceback.print_exc())


# 获取用户关联的微博超话
def get_super_topic(cookie, super_topic_id, since_id):
    sleep = random.randint(1, 60)
    print('Sleep seconds: ', sleep)
    time.sleep(sleep)
    base_url = 'https://m.weibo.cn/api/container/getIndex?'
    headers = {
        'Host': 'm.weibo.cn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'cookie': cookie  # param
    }
    params1 = {
        'containerid': f'{super_topic_id}_-_sort_time'  # param
    }
    # 存在since_id
    params2 = {
        'containerid': f'{super_topic_id}_-_sort_time',  # param
        'since_id': since_id  # param
    }
    if since_id:
        url = base_url + urlencode(params2)
    else:
        url = base_url + urlencode(params1)
    print(url)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # 获取当前页微博信息
            card_items = response.json().get('data').get('cards')
            pic_list = []
            result_list = []
            for card_item in card_items:
                card_groups = card_item.get('card_group')
                for item in card_groups:
                    if item.get('card_type') == '9':
                        item = item.get('mblog')
                        time.sleep(1)
                        create_time = get_post_time(item.get('id'))
                        # print('create_time: ', create_time)
                        if compare_time(create_time) < 0:
                            # 将结果写入csv文件
                            today = str(datetime.date.today())
                            csv_path = getcwd() + f'\\{super_topic_id}_{today}.csv'
                            df = pd.DataFrame(result_list)
                            print(since_id)
                            if since_id == '':
                                df.to_csv(csv_path, mode='w', index=False, header=True, encoding='utf-8_sig')
                            else:
                                df.to_csv(csv_path, mode='a', index=False, header=False, encoding='utf-8_sig')
                            print(u'超话获取结束')
                            return None
                        else:
                            posts = {}
                            posts['id'] = item.get('id')
                            posts['user'] = str(item.get('user')['id'])  # 发帖子的用户的id
                            posts['text'] = item.get('text')  # 文字
                            posts['reposts_count'] = item.get('reposts_count')  # 转发数量
                            posts['comments_count'] = item.get('comments_count')  # 评论数量
                            posts['attitudes_count'] = item.get('attitudes_count')  # 点赞数量
                            posts['created_at'] = create_time  # 创建时间
                            posts['isLongText'] = item.get('isLongText')  # 是否isLongText
                            posts['is_imported_topic'] = item.get('is_imported_topic')  #
                            posts['pic_num'] = item.get('pic_num')  # 图片数量
                            posts['mblog_vip_type'] = item.get('mblog_vip_type')  #
                            posts['mblogtype'] = item.get('mblogtype')  #
                            posts['mlevel'] = item.get('mlevel')  #
                            posts['source'] = item.get('source')  #
                            # 如果isLongText=true, 则获取全文
                            if item.get('isLongText'):
                                extend_id = re.findall(r'href="/status/(.+?)"', posts['text'])[0]
                                posts['text'] = get_longtext(extend_id)
                            else:
                                posts['text'] = pq(item.get('text')).text().replace('\n', '.')
                            # print(posts)
                            result_list.append(posts)
                            # 如果图片的数量大于0，则爬取图片url
                            if item.get('pic_num') > 0:
                                for pic in item.get('pics'):
                                    pic_url = pic['large']['url']
                                    pic_list.append(pic_url)
            # 将结果写入csv文件
            today = str(datetime.date.today())
            csv_path = getcwd() + f'\\{super_topic_id}_{today}.csv'
            df = pd.DataFrame(result_list)
            print(since_id)
            if since_id == '':
                df.to_csv(csv_path, mode='w', index=False, header=True, encoding='utf-8_sig')
            else:
                df.to_csv(csv_path, mode='a', index=False, header=False, encoding='utf-8_sig')

            # 获取since_id, 用于下一页request
            since_id = response.json().get('data').get('pageInfo').get('since_id')
            # print('since_id: ', since_id)
            return get_super_topic(super_topic_id, since_id)
    except requests.ConnectionError as e:
        print('Error: ', e.args)


# 获取用户基本资料：账号信息，个人信息
def get_user_basicinfo(uid, cookie):
    base_url = 'https://m.weibo.cn/api/container/getIndex?'
    # 要加cookie才能获取完整的基本资料，否则只能获取到前2项
    headers = {
        'Host': 'm.weibo.cn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'cookie': cookie
    }
    containerid = '230283' + str(uid) + '_-_INFO'
    lfid = '230283' + str(uid)
    params = {
        'containerid': containerid,  # param
        'title': '基本资料',
        'luicode': '10000011',
        'lfid': lfid  # param
    }
    url = base_url + urlencode(params)
    try:
        time.sleep(1)
        response = requests.get(url, headers=headers)
        if response.status_code == 200 and response.json().get('ok') == 1:
            account_items = response.json().get('data').get('cards')[0].get('card_group')
            person_items = response.json().get('data').get('cards')[1].get('card_group')
            basic_info = {'注册时间': '', '阳光信用': '', '生日': '', '感情状况': '', '所在地': '', '家乡': '', '公司': ''}
            for account_item in account_items:
                if account_item.get('card_type') == 41:
                    if account_item.get('item_name') == '注册时间':
                        basic_info['注册时间'] = account_item.get('item_content')
                    elif account_item.get('item_name') == '阳光信用':
                        basic_info['阳光信用'] = account_item.get('item_content')
                    # key = account_item.get('item_name')
                    # value = account_item.get('item_content')
                    # basic_info.update({key: value})
            for person_item in person_items:
                if person_item.get('card_type') == 41:
                    if person_item.get('item_name') == '生日':
                        basic_info['生日'] = person_item.get('item_content')
                    elif person_item.get('item_name') == '感情状况':
                        basic_info['感情状况'] = person_item.get('item_content')
                    elif person_item.get('item_name') == '所在地':
                        basic_info['所在地'] = person_item.get('item_content')
                    elif person_item.get('item_name') == '家乡':
                        basic_info['家乡'] = person_item.get('item_content')
                    elif person_item.get('item_name') == '公司':
                        basic_info['公司'] = person_item.get('item_content')
                    elif person_item.get('item_name') in ('大学', '高中', '中专技校', '初中', '小学', '高职', '海外'):
                        key = person_item.get('item_name')
                        value = person_item.get('item_content')
                        basic_info.update({key: value})
            return basic_info
    except Exception as e:
        print(traceback.print_exc())


# 获取博主关注的人
def get_followers(uid, cookie, page_num):
    base_url = 'https://m.weibo.cn/api/container/getSecond?'
    headers = {
        'Host': 'm.weibo.cn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'cookie': cookie
    }
    params = {
        'containerid': f'100505{uid}_-_FOLLOWERS',  # param
        'page': page_num
    }
    url = base_url + urlencode(params)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            items = response.json().get('data').get('cards')
            for item in items:
                item = item.get('user')
                followers = {}
                followers['id'] = item.get('id')
                followers['screen_name'] = item.get('screen_name')  # 姓名
                followers['gender'] = item.get('gender')  # 性别：f为女，m为男
                followers['statuses_count'] = item.get('statuses_count')  # 发过的博客数量
                followers['verified'] = item.get('verified')  # 是否认证
                followers['verified_type'] = item.get('verified_type')  # -1 为没认证；0为个人认证；其余为企业认证
                followers['verified_type_ext'] = item.get('verified_type_ext')  # 1为橙色V；0为黄色V
                followers['verified_reason'] = item.get('verified_reason')  # 认证说明
                followers['mbrank'] = item.get('mbrank')  # 会员等级
                followers['mbtype'] = item.get('mbtype')  # 会员类型：12都是个人账户，0也是。2有个人账户也有企业账户，11也是企业账户
                followers['urank'] = item.get('urank')  # 用户等级
                followers['follow_count'] = item.get('follow_count')  # 关注数量
                followers['followers_count'] = item.get('followers_count')  # 粉丝数量
                followers['description'] = item.get('description')  # 简介
                # 获取更多基本资料
                more_info = get_user_basicinfo(item.get('id'))
                followers.update(more_info)
                yield followers
    except Exception as e:
        print(traceback.print_exc())


# 获取博主的粉丝
def get_fans(uid, cookie, page_num):
    base_url = 'https://m.weibo.cn/api/container/getSecond?'
    headers = {
        'Host': 'm.weibo.cn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'cookie': cookie
    }
    params = {
        'containerid': f'100505{uid}_-_FANS',  # param
        'page': page_num
    }
    url = base_url + urlencode(params)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            fans_list =[]
            items = response.json().get('data').get('cards')
            for item in items:
                item = item.get('user')
                fans = {}
                fans['id'] = item.get('id')
                fans['screen_name'] = item.get('screen_name')  # 姓名
                fans['gender'] = item.get('gender')  # 性别：f为女，m为男
                fans['statuses_count'] = item.get('statuses_count')  # 发过的博客数量
                fans['verified'] = item.get('verified')  # 是否认证
                fans['verified_type'] = item.get('verified_type')  # -1 为没认证；0为个人认证；其余为企业认证
                fans['mbrank'] = item.get('mbrank')  # 会员等级
                fans['mbtype'] = item.get('mbtype')  # 会员类型：0, 12都是个人账户；2有个人账户也有企业账户；11是企业账户
                fans['urank'] = item.get('urank')  # 用户等级
                fans['follow_count'] = item.get('follow_count')  # 关注数量
                fans['followers_count'] = item.get('followers_count')  # 粉丝数量
                fans['description'] = item.get('description')  # 简介
                # 获取更多基本资料
                more_info = get_user_basicinfo(item.get('id'))
                fans.update(more_info)
                fans_list.append(fans)
            # 将结果写入csv文件
            csv_path = getcwd() + f'\\{uid}_fans.csv'
            df = pd.DataFrame(fans_list)
            if page_num == 1:
                df.to_csv(csv_path, mode='w', index=False, header=True, encoding='utf-8_sig')
            else:
                df.to_csv(csv_path, mode='a', index=False, header=False, encoding='utf-8_sig')
    except Exception as e:
        print(traceback.print_exc())


# 获取博主全部的粉丝
def get_fans_all(uid, cookie):
    page_num = 1
    while page_num:
        print('Begin getting data of page: ', page_num)
        base_url = 'https://m.weibo.cn/api/container/getSecond?'
        headers = {
            'Host': 'm.weibo.cn',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'cookie': cookie
        }
        params = {
            'containerid': f'100505{uid}_-_FANS',  # param
            'page': page_num
        }
        url = base_url + urlencode(params)
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200 and response.json().get('ok') == 1:
                fans_list = []
                items = response.json().get('data').get('cards')
                for item in items:
                    item = item.get('user')
                    fans = {}
                    fans['id'] = item.get('id')
                    fans['screen_name'] = item.get('screen_name')  # 姓名
                    fans['gender'] = item.get('gender')  # 性别：f为女，m为男
                    fans['statuses_count'] = item.get('statuses_count')  # 发过的博客数量
                    fans['verified'] = item.get('verified')  # 是否认证
                    fans['verified_type'] = item.get('verified_type')  # -1 为没认证；0为个人认证；其余为企业认证
                    fans['mbrank'] = item.get('mbrank')  # 会员等级
                    fans['mbtype'] = item.get('mbtype')  # 会员类型：0, 12都是个人账户；2有个人账户也有企业账户；11是企业账户
                    fans['urank'] = item.get('urank')  # 用户等级
                    fans['follow_count'] = item.get('follow_count')  # 关注数量
                    fans['followers_count'] = item.get('followers_count')  # 粉丝数量
                    fans['description'] = item.get('description')  # 简介
                    # 获取更多基本资料
                    more_info = get_user_basicinfo(item.get('id'), cookie)
                    fans.update(more_info)
                    fans_list.append(fans)
                # 将结果写入csv文件
                csv_path = getcwd() + f'\\{uid}_fans.csv'
                df = pd.DataFrame(fans_list)
                if page_num == 1:
                    df.to_csv(csv_path, mode='w', index=False, header=True, encoding='utf-8_sig')
                else:
                    df.to_csv(csv_path, mode='a', index=False, header=False, encoding='utf-8_sig')
            else:
                # response.json().get('ok') == 0时结束
                print('End')
                return None
        except requests.ConnectionError as e:
            print('Error: ', e.args)
        # 该轮循环结束，page_num增加1，进入下一轮循环
        print('End getting data of page: ', page_num)
        page_num = page_num + 1
        # random sleep
        sleep = random.randint(10, 120)
        print('Sleep seconds: ', sleep)
        time.sleep(sleep)


# 获取当前/每日微博热搜50条
def get_realtime_hot():
    base_url = 'https://m.weibo.cn/api/container/getIndex?'
    headers = {
        'Host': 'm.weibo.cn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    extparam = 'cate=10103&pos=0_0&mi_cid=100103&filter_type=realtimehot&c_type=30&display_time=' + str(int(time.time()))
    print(extparam)
    params = {
        'containerid': '106003type=25&t=3&disable_hot=1&filter_type=realtimehot',
        'title': '微博热搜',
        'extparam': extparam,
        'luicode': '10000011',
        'lfid': '231583'
    }
    url = base_url + urlencode(params)
    print(url)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            items = response.json().get('data').get('cards')[0].get('card_group')
            for item in items:
                hot = {}
                hot['pic'] = re.findall(r'_img_search_(.+?).png', item.get('pic'))[0]  # 话题排名图片：0，1，2，3，……50
                hot['desc'] = item.get('desc')  # 话题描述
                if 'desc_extr' in item:
                    hot['desc_extr'] = item.get('desc_extr')  # 话题被讨论数量，不是所有的都有这个字段，第0条置顶话题没有
                else:
                    hot['desc_extr'] = ''
                if 'icon' in item:
                    hot['icon'] = re.findall(r'_(.+?).png', item.get('icon'))[0]  # 话题状态图片：沸，热，不是所有的都有这个字段
                else:
                    hot['icon'] = ''
                yield hot
    except requests.ConnectionError as e:
        print('Error: ', e.args)


if __name__ == '__main__':
    uid = '2803301701'  # 待获取的用户的uid
    cookie = ''  # 当前登录的用户的cookie
    # 获取某用户的超话
    # super_topic_id = get_super_topic_id(uid, cookie)
    # get_super_topic(cookie, super_topic_id, '')

    # 获取某用户的粉丝
    # for page_num in range(1, 3):
    #     get_fans(uid, cookie, page_num)

    # 获取关注的人
    # for page_num in range(1, 3):
    #     followers = get_followers(uid, cookie, page_num)
    #     for follower in followers:
    #         print(follower)

    # 获取微博热搜
    # hots = get_realtime_hot()
    # for hot in hots:
    #     print(hot)

    # 获取用户的微博文字和图片url
    # for page_num in range(1, 3):
    #     weibo_list, pic_list = get_user_weibo(uid, cookie, page_num)
    #     # 保存解析结果到csv文档
    #     save_result(uid, page_num, weibo_list)
    #     # 保存图片url到txt文档
    #     save_url(uid, page_num, pic_list)
