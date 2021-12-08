import sys

# if 'timan102' in os.uname().nodename:
#     og_model_dir = '/srv/data/judel/models'
#     og_data_dir = '/home/bhavya2/juvenile/data'
#     base_dir = '/home/adavies4/judel'
#
# elif 'timan103' in os.uname().nodename:
#     base_dir = '/srv/scratch/adavies4/judel'
#
# else:
#     raise Error('Must be run on timan{102,103}')

og_model_dir = old_model_dir = '/srv/data/judel/models'
og_data_dir = old_data_dir = '/home/bhavya2/juvenile/data'

base_dir = '/home/adavies4/judel'
src_dir = f'{base_dir}/src'
new_model_dir = f'{base_dir}/models'
new_data_dir = f'{base_dir}/data'

ccla_path = f'{src_dir}/ccla'

for path in [ccla_path]:
    sys.path.extend(path)
