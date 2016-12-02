#!/usr/bin/env python


import sys
import re
import os
import datetime
import argparse


# configuration variables:
DIRVISH_CONFIG="/etc/dirvish/master.conf"
CRON_HOUR = 1
CRON_MINUTE = 30


def get_arguments():
    parser = argparse.ArgumentParser(description='Checks dirvish backup status.')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', \
            help="show detailed information")
    return parser.parse_args()


def read_config(config):
    try:
        in_file = open(config, 'r')
    except:
        print "Cannot open dirvish config file."
        sys.exit(3)
    lines = in_file.readlines()
    in_file.close()
    return lines


def get_list(name, lines): 
    item_list = []
    for line in lines:
        if line.startswith(name + ":"):
            list_begin = lines.index(line) + 1
            break
    for line in lines[list_begin:]:
        if not line[0].isspace() and not line[0] == "#":
            list_end = lines.index(line)
            break
    for line in lines[list_begin:list_end]:
        if re.match("^\s+(?!#)\S", line):
            item_list.append(line.split()[0])
    return item_list


def form_dirs(banks, vaults):
    combinations = []
    vault_to_dir = {}
    for bank in banks:
        for vault in vaults:
            combinations.append([vault, bank + "/" + vault])
    for combo in combinations:
        if os.path.isdir(combo[1]):
            if combo[0] in vault_to_dir.keys():
                print combo[0], 'is in two or more banks!'
                sys.exit(3)
            else:
                vault_to_dir[combo[0]] = combo[1]
    return vault_to_dir


def get_date(hour, minute):
    if datetime.datetime.now().hour < hour or \
        (datetime.datetime.now().hour == hour and \
        datetime.datetime.now().minute <= minute):
        date = datetime.date.today() - datetime.timedelta(days = 1)
    else:
        date = datetime.date.today()
    if date.month < 10:
        month = "0" + str(date.month)
    else:
        month = str(date.month)
    if date.day < 10:
        day = "0" + str(date.day)
    else:
        day = str(date.day)
    return str(date.year) + month + day


def sort_vaults(dirs, date):
    state_to_vaults = {"finished" : [], "incomplete" : [], "notstarted" : []}
    for vault in dirs.keys():
        if os.path.isdir(dirs[vault] + "/" + date):
            if os.path.isfile(dirs[vault] + "/" + date + "/log.gz"):
                state_to_vaults["finished"].append(vault)
            else:
                state_to_vaults["incomplete"].append(vault)
        else:
            state_to_vaults["notstarted"].append(vault)
    return state_to_vaults


def find_running():
    running = []
    processes = os.popen('ps auxww | grep dirvish').readlines()
    for process in processes:
        if re.search("--vault", process):
            running.append(re.search('(?<=--vault\s)\S*', process).group())
    return running


def check_vaults(state_to_vaults, running):
    status = {'exit' : 1, 'messages' : []}
    if running:
        failed = [vault for vault in state_to_vaults['incomplete'] if \
                vault not in running]
        if failed:
            status['exit'] = 2
            status['messages'] = ['backup runing, failed so far ' + str(failed)]
        else:
            status['exit'] = 0
            status['messages'] = ['backup running, nothing failed so far.']
    else:
        failed = state_to_vaults['incomplete']
        notstarted = state_to_vaults['notstarted']
        if failed:
            status['exit'] = 2
            status['messages'].append('vaults failed ' + str(failed))
        if notstarted:
            status['exit'] = 2
            status['messages'].append('vaults not started ' + str(notstarted))
        if not failed and not notstarted:
            status['exit'] = 0
            status['messages'] = ['all vaults completed.']
    return status


def conclude(exit):
        conclusions = {0 : 'OK:', 1 : 'WARNING:', 2 : 'CRITICAL:', 3 : 'UNKNOWN:'}
        return conclusions[exit]


def print_verbose(banks, vaults, vault_to_dir, state_to_vaults, running):
    print '%-20s | %-10s | %-7s | %-30s' %\
            ('vault', 'state', 'running', 'path')
    print '-' * 21 + '+' + '-' * 12 + '+' + '-' * 9 + '+' + '-' * 31
    for state in state_to_vaults.keys():
        for vault in state_to_vaults[state]:
            if vault in running:
                is_running = 'running'
            else:
                is_running = 'no'
            print '%-20s | %-10s | %-7s | %-30s' %\
                    (vault, state, is_running, vault_to_dir[vault] )
    print '-' * 57

def run_all():
    args = get_arguments()
    lines = read_config(DIRVISH_CONFIG)
    banks = get_list("bank", lines)
    vaults = get_list("Runall", lines)
    vault_to_dir = form_dirs(banks, vaults)
    date = get_date(CRON_HOUR, CRON_MINUTE)
    state_to_vaults = sort_vaults(vault_to_dir, date)
    running = find_running()
    status = check_vaults(state_to_vaults, running)
    if args.verbose:
        print_verbose(banks, vaults, vault_to_dir, state_to_vaults, running)
    exit = status['exit']
    messages = status['messages']
    conclusion = conclude(exit)
    print conclusion, messages[0]
    if len(messages) > 1:
        for message in messages[1:]:
            print message
    sys.exit(exit)
    
    
if __name__ == '__main__':
    run_all()
