# /**
#  * @author Emmanuel David Castillo
#  * @email ecastillo@sgc.gov.co-ecastillot@unal.edu.co
#  * @create date 2021-06-04 07:09:26
#  * @modify date 2021-07-04 09:29:01
#  * @desc [description]
#  */


import os
import argparse
import time
import datetime as dt
from typing import DefaultDict
import pandas as pd
import subprocess as sp
import concurrent.futures as cf
from colorama import Fore, Back, Style

RSNC_path = os.path.join(os.getcwd(),"csv","rsnc.csv")
RNAC_path = os.path.join(os.getcwd(),"csv","rnac.csv")
INTER_path = os.path.join(os.getcwd(),"csv","inter.csv")

DEFAULT_args = {'online':None,'delta_time':120,'server':"232",
                'network':None,'location':None,'status':None,'add':None}


def do_slinktool(network,station=None,location=None,channel=None,
                level="network",server="232",save=None):
    """
    Parameters:
    -----------
    network : str
        Name of the network
    station: str
        Name of the station
    location: str
        Location code 
    channel: str
        channel information
    level: str
        "network","station","only_station","location","channel"
    server: str (default:232)
        232,13,222
    save: None or str (default:None)
        If it's different to None else it take save variable as path of the output file
    """

    if level == "network":
        _msg = f"{network}"
    elif level == "station":
        _msg = f"{network} {station}"
    elif level == "only_station":
        _msg = f"{station}"
    elif level == "location":
        _msg = f"{network} {station} {location}"
    elif level == "channel":
        _msg = f"{network} {station} {location} {channel}"
    else:
        raise Exception(f"level: {level} no encontrado")

    msg = f"slinktool -Q 10.100.100.{server}:16501 |grep '{_msg}'"
    
    if save!= None:
        if os.path.isdir(os.path.dirname(save)):
            pass
        else:
            os.makedirs(os.path.dirname(save))
        msg += f">{save}"

    # print(msg)
    slinktool = sp.getoutput(msg)

    if not slinktool:
        # print(f"No se encuentra: {_msg} ")
        slinktool = None

    return slinktool

def get_currentdate(network,station=None,location=None,channel=None,
                     level="network",server="232"):
    """
    Parameters:
    -----------
    network : str
        Name of the network
    station: str
        Name of the station
    location: str
        Location code 
    level: str
        "network","station","location"
    server: str (default:232)
        232,13,222

    Returns:
    --------
    date: datetime
        current datetime information
    """
    slinktool = do_slinktool(network,station,location,channel,level,server)

    if slinktool == None:
        currentdate = dt.datetime.strptime("2020/01/01 00:00:00.0000", '%Y/%m/%d %H:%M:%S.%f')
    else:
        currentdate = slinktool.split('-')[-1].strip()
        currentdate = dt.datetime.strptime(currentdate, '%Y/%m/%d %H:%M:%S.%f')
    return currentdate

def do_checklist(csv,sec=600,server="232",level="channel"):
    info = pd.read_csv(csv, dtype=object) #dtype=object to read all as string
    

    info["network"] = info["network"].map( lambda x: x.strip().ljust(2) )
    info["station"] = info["station"].map( lambda x: x.strip().ljust(5) )
    info["location"] = info["location"].map( lambda x: x.strip().ljust(2) )
    info["channel"] = info["channel"].map( lambda x: x.strip().ljust(3) )

    exe = lambda row: get_currentdate(row["network"],row["station"],row["location"]
                                    ,row["channel"], level=level,server=server)
    info["first_slinktool"] = info.apply( exe,axis=1 )
    today = dt.datetime.utcnow()

    # print("Espere 15 segundos")
    time.sleep(15)
    info["second_slinktool"] = info.apply( exe,axis=1 )
    
    info = info.dropna()

    delta = lambda row: (row["second_slinktool"]-row["first_slinktool"]).seconds
    info["delta_slinktool"] = info.apply(delta ,axis=1 )

    current_delta = lambda row: (today-row["first_slinktool"]).seconds
    info["current_delta"] = info.apply(current_delta ,axis=1 )



    def get_status(current_delta,delta,sec):
        if current_delta > sec:
            if delta == 0:
                status = "offline"
            elif delta >= 0:
                status = "recovering"
            else:
                status = None
        else:
            status = "online"
        return status


    status = lambda row: get_status(row["current_delta"],row["delta_slinktool"],sec)
    info["status"] = info.apply( status,axis = 1)

    df = info[["network","station","location","channel","status"]]
    

    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    #     print(df)
    return df

def run(sec=600,server="232",filter_network=None,
        filter_location=None,filter_status=None):

    def run_checklist(args):
        '''
        args: tuple
            (csv,level): path of the csv and the level to do the slinktool 
        '''
        csv, level = args
        df = do_checklist(csv,sec,server,level)
        return df

    def get_status_color(value):
        """
        Colors elements in a dateframe
        green if online and red if
        ooffline. Does not color NaN
        values.
        """

        if value == "offline":
            color = Fore.RED
        elif value == "recovering":
            color = Fore.MAGENTA
        elif value == "online":
            color = Fore.GREEN
        else:
            color = Fore.BLACK

        return color + str(value) + Style.RESET_ALL

    def get_station_color(value):
        """
        Colors elements in a dateframe
        yellow if RSNC and blue if
        RNAC.
        """

        if value in ("00","20","  ","40"):
            color = Fore.YELLOW
        elif value in ("10","11","30"):
            color = Fore.BLUE
        else:
            color = Fore.BLACK
        return color + str(value) + Style.RESET_ALL

    paths = [(RSNC_path,"channel"),(RNAC_path,"channel"),(INTER_path,"only_station")]
    with cf.ThreadPoolExecutor(3) as executor:
        dfs = list(executor.map(run_checklist,paths)) ##cambiar

    checklist_df = pd.concat(dfs,ignore_index=True)

    if filter_network != None:
        checklist_df = checklist_df[checklist_df["network"].isin(filter_network)]

    if filter_location != None:
        checklist_df = checklist_df[checklist_df["location"].isin(filter_location)]

    if filter_status != None:
        checklist_df = checklist_df[checklist_df["status"].isin(filter_status)]

    checklist_df['status'] = checklist_df['status'].apply(get_status_color)
    checklist_df['location'] = checklist_df['location'].apply(get_station_color)

    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        os.system("clear")
        print(checklist_df)

def time_real_run(chunktime,sec=600,server="232",filter_network=None,
                filter_location=None,filter_status=None):
    while True:
        run(sec,server,filter_network,
                            filter_location,filter_status)
        time.sleep(chunktime)

def read_args():
    prefix = "+"

    parser = argparse.ArgumentParser("Checklist. ",prefix_chars=prefix)

    parser.add_argument(prefix+"online",prefix*2+"online",
                        default=DEFAULT_args['online'],
                        type=float,
                        metavar='',
                        help="Tiempo de actualización en segundos")

    parser.add_argument(prefix+"dt",prefix*2+"delta_time",
                        default=DEFAULT_args['delta_time'],
                        type=float,
                        metavar='',
                        help="Limite de tiempo en segundos para decir que esta por fuera")

    parser.add_argument(prefix+"server",prefix*2+"server",
                        default=DEFAULT_args['server'],
                        type=str,
                        metavar='',
                        help="Servidor donde se hace la consulta")

    parser.add_argument(prefix+"net",prefix*2+"network",
                        default=DEFAULT_args['network'],
                        nargs='+',
                        metavar='',
                        help= "Filtrar por redes. Ejemplo: 'CM' 'OM' 'OP' ")

    parser.add_argument(prefix+"loc",prefix*2+"location",
                        default=DEFAULT_args['location'],
                        nargs='+',
                        metavar='',
                        help="Filtrar por localización. Ejemplo: '00' '  ' '20' ")

    parser.add_argument(prefix+"status",prefix*2+"status",
                        default=DEFAULT_args['status'],
                        nargs='+',
                        metavar='',
                        help="Filtrar por estado. Ejemplo: 'offline' 'recovering' ")

    parser.add_argument(prefix+"a",prefix*2+"add",
                        default=DEFAULT_args['add'],
                        metavar='',
                        choices=["RSNC","RNAC","INTER"],
                        help="Agregar información en RSNC, RNAC o INTER ")

    args = parser.parse_args()
    vars_args = vars(args)
    return vars_args

def main(args):

    if args["add"] != None:
        if args["add"] in ("RSNC","rsnc"):
            os.system(f"nano {RSNC_path}")
        elif args["add"] in ("RNAC","rnac"):
            os.system(f"nano {RNAC_path}")
        elif args["add"] in ("INTER","inter"):
            os.system(f"nano {INTER_path}")
        else:
            add = args["add"]
            msg = f"add: {add} no existe"
            raise Exception(msg)

        exit()

    if args['online'] != None:
        time_real_run(args['online'],args['delta_time'],args['server'],
                    args['network'],args['location'],args['status'])

    else:
        run(args['delta_time'],args['server'],
                    args['network'],args['location'],args['status'])

if __name__ == "__main__":
    # do_slinktool("CM","ROSC"," ","location","232","/mnt/almacenamiento/Emmanuel_Castillo/git_EDCT/SGC/checklist/slinktools/rsnc_1.dat")
    # get_currentdate("CM","ROSC","  ","BHZ","channel","232")
    # do_slinktool("CM","ROSC","  ","BHZ","channel","232")

    # do_checklist("/mnt/almacenamiento/Emmanuel_Castillo/git_EDCT/SGC/checklist/rsnc.csv")

    # print("BET".ljust(5)+"hola")
    # print("APAC".ljust(5)+"hola")

    # run(600,"232",None,None,["offline","recovering","online"])
    #time_real_run(5,600,"232",["CM"],None,["offline","recovering"])

    # df = pd.read_csv("/mnt/almacenamiento/Emmanuel_Castillo/git_EDCT/SGC/checklist/csv/inter.csv")
    # df = df.sort_values(by=['station'],ignore_index=True)
    # df.to_csv("/mnt/almacenamiento/Emmanuel_Castillo/git_EDCT/SGC/checklist/csv/inter_sort.csv",index=False)
    print("Espere 30 segundos")
    args = read_args()
    main(args)
