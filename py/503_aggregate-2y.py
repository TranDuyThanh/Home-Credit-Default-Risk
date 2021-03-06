#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 18:39:07 2018

@author: kazuki.onodera

based on
https://www.kaggle.com/jsaguiar/updated-0-792-lb-lightgbm-with-simple-features/code
"""

import numpy as np
import pandas as pd
import gc
import os
from multiprocessing import Pool, cpu_count
NTHREAD = cpu_count()
import utils_agg
import utils
utils.start(__file__)
#==============================================================================
PREF = 'f503_'

KEY = 'SK_ID_CURR'

day_start = -365*2 # -2922
day_end   = -365*1 # -2922

os.system(f'rm ../feature/t*_{PREF}*')
# =============================================================================
# 
# =============================================================================
bure = utils.read_pickles('../data/bureau')
bure = bure[bure['DAYS_CREDIT'].between(day_start, day_end)]

col_cat = ['CREDIT_ACTIVE', 'CREDIT_CURRENCY', 'CREDIT_TYPE']

train = utils.load_train([KEY])
test = utils.load_test([KEY])

# =============================================================================
# 
# =============================================================================
def aggregate():
    
    df = utils.get_dummies(bure)
    
    li = []
    for c1 in df.columns:
        for c2 in col_cat:
            if c1.startswith(c2+'_'):
                li.append(c1)
                break
    
    cat_aggregations = {}
    for cat in li:
        cat_aggregations[cat] = ['mean', 'sum']
    
    df_agg = df.groupby(KEY).agg({**utils_agg.bure_num_aggregations, **cat_aggregations})
    df_agg.columns = pd.Index([e[0] + "_" + e[1] for e in df_agg.columns.tolist()])
    
    # std / mean
    col_std = [c for c in df_agg.columns if c.endswith('_std')]
    for c in col_std:
        df_agg[f'{c}-d-mean'] = df_agg[c]/df_agg[c.replace('_std', '_mean')]
    
    # max / min
    col_max = [c for c in df_agg.columns if c.endswith('_max')]
    for c in col_max:
        try:
            df_agg[f'{c}-d-min'] = df_agg[c]/df_agg[c.replace('_max', '_min')]
            df_agg[f'{c}-m-min'] = df_agg[c]-df_agg[c.replace('_max', '_min')]
        except:
            pass
    
    df_agg['BURE_COUNT'] = df.groupby(KEY).size()
    df_agg.reset_index(inplace=True)
    
    tmp = pd.merge(train, df_agg, on=KEY, how='left').drop(KEY, axis=1)
    utils.to_feature(tmp.add_prefix(PREF), '../feature/train')
    
    tmp = pd.merge(test, df_agg, on=KEY, how='left').drop(KEY, axis=1)
    utils.to_feature(tmp.add_prefix(PREF),  '../feature/test')
    
    return


# =============================================================================
# main
# =============================================================================

aggregate()



#==============================================================================
utils.end(__file__)
