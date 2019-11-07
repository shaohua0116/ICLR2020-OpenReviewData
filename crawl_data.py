import numpy as np
import h5py
import string
from util import crawl_meta

CRAWL_DATA = True
AFTER_DECISION = False
CRAWL_REVIEW = True

# Get the meta data
meta_list = crawl_meta(meta_hdf5=None, write_meta_name='data.hdf5', crawl_review=CRAWL_REVIEW)
num_withdrawn = len([m for m in meta_list if m.withdrawn or m.desk_reject])
print('Number of submissions: {} (withdrawn/desk reject submissions: {})'.format(
    len(meta_list), num_withdrawn))
