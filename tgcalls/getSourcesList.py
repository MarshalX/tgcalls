import os

SRC_DIR = 'src'

if __name__ == '__main__':
    sources = list()
    for root, _, files in os.walk(SRC_DIR):
        sources += [f'${{src_loc}}{root[len(SRC_DIR):]}/{file}' for file in files]

    print('\n'.join(sources))
