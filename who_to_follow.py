import soundcloud
import math

def get_followers(name):
    followings=[]
    user = client.get('/users/' + name)
    count = user.followings_count
    loop_count = math.ceil(count/50)
    for i in range(loop_count):
        followings.extend(client.get('/users/' + name + '/followings', offset=50*i))
    return followings

def build_table(following):
    freq_table = {}
    for i in following:
        print(i.permalink, end="")
        followings=get_followers(i.permalink)
        #print(i.permalink)
        for j in followings:
            if j.permalink in freq_table:
                print('+', end="")
                freq_table[j.permalink] += 1
            else:
                print('0', end="")
                freq_table[j.permalink] = 1
        print('')
    return freq_table

def print_table(freq_table, followings):
    magic_from_SO = sorted( ((v,k) for k,v in freq_table.items()), reverse=True)
    follow_list=[]

    for i in followings:
        follow_list.append(i.permalink)


    for i in magic_from_SO:
        if i[0] < 3:
            break
        if i[1] not in follow_list:
            print('+', end="")
        print(i[1] , ":" , i[0])


client = soundcloud.Client(client_id="f367f38aa03863c376a626bcbab2e126")
followings = get_followers('jakkdl')
table = build_table(followings)
print_table(table, followings)
