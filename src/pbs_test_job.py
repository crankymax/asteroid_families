import time
import sys


def long_wait(*args):
    time.sleep(1*60)
    return True


if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) >= 4:
        sim_no = sys.argv[1]

        run_length = float(sys.argv[2])
        inp_dir = sys.argv[3]
        if len(sys.argv) == 5:
            max_walltime = float(sys.argv[4])
        else:
            max_walltime = 168.0
        print(f'parameters {sim_no} {run_length} {inp_dir} {max_walltime}')
        exit(long_wait(inp_dir, sim_no, run_length, max_walltime))
