#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 27 02:08:31 2018

@author: Kazuki
"""

import pandas as pd
import numpy as np
import utils, os
#utils.start(__file__)
#==============================================================================
PREF = 'f024_'

path_user_id = '../data/user_id_v5.csv.zip'

KEY = 'SK_ID_CURR'

os.system(f'rm ../feature/t*_{PREF}*')
#==============================================================================

user_id = pd.read_csv(path_user_id)

user_unq = user_id[user_id.user_id==1]
user_dup = user_id[user_id.user_id!=1]

start = user_dup.user_id.max()+1
user_unq['user_id'] = range(start, start+user_unq.shape[0])

user_id = pd.concat([user_unq, user_dup])
user_id.to_csv(path_user_id.replace('zip', 'gz'), index=False, compression='gzip')

train  = pd.read_csv('../input/application_train.csv.zip')
train['is_train'] = 1

test  = pd.read_csv('../input/application_test.csv.zip')
test['is_train'] = 0

trte = pd.concat([train, test], ignore_index=True)

dup = user_id[user_id.duplicated('user_id', False)]
cnt = dup.groupby('user_id').size()
cnt.name = 'dup_cnt'
cnt = cnt.reset_index()
cnt['dup_id'] = range(cnt.shape[0])

dup = pd.merge(dup, cnt, on='user_id', how='left')
dup = pd.merge(dup, trte, on=KEY, how='left')

col = train.columns.tolist() + [c for c in dup.columns if c not in train.columns]

dup = dup[col]





dup.loc[dup['DAYS_EMPLOYED']==365243, 'DAYS_EMPLOYED'] = np.nan

dup['seq'] = 1
dup['seq'] = dup.groupby('dup_id').seq.cumsum()-1

category = dup.select_dtypes('O').columns
dup = pd.get_dummies(dup, columns=category)


col = dup.columns.tolist()
for c in ['dup_id', 'dup_cnt', 'user_id']:
    col.remove(c)
col = ['user_id'] + col


# =============================================================================
# 
# =============================================================================
dup.sort_values(['user_id', 'DAYS_BIRTH'], ascending=[True, False], inplace=True)
#dup.sort_values(['user_id', 'DAYS_REGISTRATION'], ascending=[True, False], inplace=True)
#dup.sort_values(['user_id', 'DAYS_BIRTH'], inplace=True)

#tmp1 = dup.sort_values(['user_id', 'DAYS_REGISTRATION'], )
#tmp2 = dup.sort_values(['user_id', 'DAYS_BIRTH'], )
#
#tmp1.equals(tmp2)


feature = dup[['SK_ID_CURR']].set_index('SK_ID_CURR')
gr = dup.groupby('dup_id')


# last
for c in col[2:]:
    feature[f'last_{c}'] = gr[c].shift(1).values
    feature[f'lastlast_{c}'] = gr[c].shift(2).values
    
    feature[f'last_{c}_r'] = gr[c].shift(-1).values
    feature[f'lastlast_{c}_r'] = gr[c].shift(-2).values

# other
for c in col[3:]:
    feature[f'{c}_diff'] = gr[c].diff(1).values
    feature[f'{c}_ratio'] = ( dup[c] / gr[c].shift(1) ).values
    feature[f'{c}_min'] = pd.concat([ dup[c], gr[c].shift(1), gr[c].shift(2)], axis=1).min(1).values
    feature[f'{c}_max'] = pd.concat([ dup[c], gr[c].shift(1), gr[c].shift(2)], axis=1).max(1).values
    feature[f'{c}_mean'] = pd.concat([ dup[c], gr[c].shift(1), gr[c].shift(2)], axis=1).mean(1).values
    
    feature[f'{c}_diff_r'] = gr[c].diff(-1).values
    feature[f'{c}_ratio_r'] = ( dup[c] / gr[c].shift(-1) ).values
    feature[f'{c}_min_r'] = pd.concat([ dup[c], gr[c].shift(-1), gr[c].shift(-2)], axis=1).min(1).values
    feature[f'{c}_max_r'] = pd.concat([ dup[c], gr[c].shift(-1), gr[c].shift(-2)], axis=1).max(1).values
    feature[f'{c}_mean_r'] = pd.concat([ dup[c], gr[c].shift(-1), gr[c].shift(-2)], axis=1).mean(1).values

feature.dropna(how='all', inplace=True)

utils.remove_feature(feature, var_limit=0, corr_limit=0.98, sample_size=19999)


train = utils.load_train([KEY])
test = utils.load_test([KEY])

feature.reset_index(inplace=True)
feature = pd.merge(feature, user_id, on=KEY, how='left')

tmp = pd.merge(train, feature, on=KEY, how='left').drop(KEY, axis=1)
utils.to_feature(tmp.add_prefix(PREF), '../feature/train')

tmp = pd.merge(test, feature, on=KEY, how='left').drop(KEY, axis=1)
utils.to_feature(tmp.add_prefix(PREF),  '../feature/test')




#==============================================================================
#utils.end(__file__)





