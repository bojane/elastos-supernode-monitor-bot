import json
import pandas as pd
import requests
from IPython.display import display, HTML
import time
import config
from posting2 import TelegramBot
import asyncio
from config import TELEGRAM_BOT_TOKEN, \
ELASTOS_ELA_USER, ELASTOS_ELA_PASS, ELASTOS_ELA_URL, \
ELASTOS_SCANDINAVIA, ELASTOS_SN_NOTIFYER, ELASTOS_TESTCHANNEL

headers = {
    'Content-Type': 'application/json',
}




def get_blockheight():
    data = '{"method": "getblockcount"}'

    try:
        #response = requests.post('http://cdb6a6d960ede64a70243dea646e5b2a:8b4d6d63169d2ea96113c44d0d2d2dc4@localhost:20336/', headers=headers, data=data)
        response = requests.post(ELASTOS_ELA_URL, headers=headers, data=data, auth=(ELASTOS_ELA_USER, ELASTOS_ELA_PASS))
        response.raise_for_status()
        print(json.loads(response.text))
        response = (json.loads(response.text))
        response=response['result']
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def get_producers_data():
    data = '{"method": "listproducers","params":{"state":"all","start":0,"limit":300}}'

    try:
        #response = requests.post('http://cdb6a6d960ede64a70243dea646e5b2a:8b4d6d63169d2ea96113c44d0d2d2dc4@localhost:20336/', headers=headers, data=data)
        response = requests.post(ELASTOS_ELA_URL, headers=headers, data=data, auth=(ELASTOS_ELA_USER, ELASTOS_ELA_PASS))
        response.raise_for_status()
        response = (json.loads(response.text))
        response=response['result']['producers']
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

    
    

async def main():
    
    chat_id = ELASTOS_TESTCHANNEL  # Replace with the actual chat ID
    message = "Starting up elaBotMain"
    bot = TelegramBot("telegram.ini")
    await bot.post_message(message, chat_id)
    

    # time between running while
    timepolling = 300

    # first time only
    producers_data = get_producers_data()
    df_old = pd.DataFrame.from_dict(producers_data)
    df_old['dposv2votes'] = pd.to_numeric(df_old['dposv2votes'])


    
    
    # --- we don't want to go inside if when blockchain is still syncing
    blockheight_old = get_blockheight()
    time.sleep(20)
    
    blockStuckCount = 0
    
    while True:
        blockheight = get_blockheight()
        producers_data = get_producers_data()

        if producers_data is not None and blockheight - blockheight_old < 10:

            # Process the data and perform comparisons
            df = pd.DataFrame.from_dict(producers_data)

            # Ensure 'dposv2votes' is numeric, not string
            df['dposv2votes'] = pd.to_numeric(df['dposv2votes'])
            
     
            df = df.sort_values(by=['dposv2votes', 'nickname'], ascending=[False, True])
            df_old = df_old.sort_values(by=['dposv2votes', 'nickname'], ascending=[False, True])
            
            #print(df)
            HTML(df.to_html(open('sn_file.html', 'w')))
            

            # -------------------------------------------------------------------------------

            # Add an 'order' column to preserve the order of rows in each DataFrame
            df['order'] = range(1, len(df) + 1)
            df_old['order'] = range(1, len(df_old) + 1)

            len_old = len(df_old)
            len_new = len(df)
            if len_old != len_new:
                print(f"Difference in length detected. Old: {len_old}, New: {len_new}")

            # --------------------  this is for catching arrival of new supernodes --------------

            if len_new > len_old:
                print("New entries have been added.")
                added_entries = set(df['nodepublickey']) - set(df_old['nodepublickey'])
                if added_entries:
                    # Filter 'df' to get the rows for added entries
                    added_rows = df[df['nodepublickey'].isin(added_entries)]
                    # Extract and print the nicknames of these added rows
                    print("Nicknames of added entries:")
                    for nickname in added_rows['nickname']:
                        print(nickname)
            elif len_new < len_old:
                print("Some entries have been removed.")
                removed_entries = set(df_old['nodepublickey']) - set(df['nodepublickey'])
                if removed_entries:
                    print(f"Removed entries' nodepublickey: {removed_entries}")
            
            # ------------------------------------------------------------------------------------



            # merged_sn_place_df is for seeing if the SN order has changed between each other
            
            # Merge the two DataFrames based on 'nickname' and 'order'
            merged_sn_place_df = pd.merge(df, df_old, on=['order'], suffixes=('_new', '_old'), how='inner')

            # Sort by 'nickname' to group the different order of 'nickname' rows
            merged_sn_place_df = merged_sn_place_df.sort_values(by='order')

            # Drop the 'order' column
            #merged_sn_place_df = merged_sn_place_df.drop('order', axis=1)

            merged_sn_place_df['sn_diff'] = merged_sn_place_df['nodepublickey_new'] != merged_sn_place_df['nodepublickey_old']

            # ------------------------------------------------------------------------------

            merged_df = df.merge(df_old, on='nodepublickey', how='inner', suffixes=('_new', '_old'))

            # Identify rows where 'state' is different
            merged_df['state_diff'] = merged_df['state_new'] != merged_df['state_old']
            # Identify rows where 'dposv2votes_diff' is different
            merged_df['dposv2votes_diff'] = merged_df['dposv2votes_new'] - merged_df['dposv2votes_old']

            # ------------------------------------------------------------------------------

            HTML(merged_df.to_html(open('sn_file_merged.html', 'w')))
            HTML(merged_sn_place_df.to_html(open('sn_file_merged_sn_place.html', 'w')))
            
            
            # ------------------- change state of SN -------------------------------
            
            # Filter for differing rows and drop duplicate 'nickname' rows
            differing_staterows = merged_df[merged_df['state_diff']]

            # Select and print only the relevant columns
            if not differing_staterows.empty:
                differing_staterows = differing_staterows[['nickname_old', 'state_new', 'state_old']]
                differing_staterows.reset_index(drop=True, inplace=True)
                print("Differing state Rows:")
                print(differing_staterows)
                chat_id = ELASTOS_SN_NOTIFYER  # Define your chat ID here
                await bot.report_differing_state(chat_id, differing_staterows)
            else:
                print("No differing state rows found.")

            # --------------------------------------------------------------------

            # ----------------------check for new supernodes -----------------------

            # Assuming 'df' is your current DataFrame and 'df_old' is the previous DataFrame

            # Get sets of unique identifiers (e.g., nodepublickeys) for current and previous data
            current_supernodes = set(df['nodepublickey'])
            previous_supernodes = set(df_old['nodepublickey'])

            # Find the difference to identify new supernodes
            new_supernodes = current_supernodes - previous_supernodes

            if new_supernodes:
                # If there are new supernodes, filter 'df' to get just those new entries

                new_supernodes_data = df[df['nodepublickey'].isin(new_supernodes)]
                
                # Here you can further process new_supernodes_data, such as formatting it for a report
                # For example, extract nicknames and other relevant info for the new supernodes
                print("New supernodes detected:", new_supernodes_data['nickname'])
                # And then send a notification about these new supernodes
                # You would need to implement or adapt a method in your TelegramBot class to handle this notification
                chat_id = ELASTOS_SN_NOTIFYER  # Define your chat ID here
                await bot.report_new_supernodes(chat_id, new_supernodes_data)  # This is a hypothetical method you'd implement
                
            else:
                print("No new supernodes detected.")

            # ----------------- change in voting ----------------------------------


            differing_voterows = differing_rows = merged_df[merged_df['dposv2votes_diff'] != 0]
  
            if not differing_voterows.empty:
                chat_id = ELASTOS_SCANDINAVIA
                HTML(differing_voterows.to_html(open('differing_voterows.html', 'w')))
                differing_voterows = differing_voterows[['nickname_old', 'dposv2votes_new', 'dposv2votes_old', 'dposv2votes_diff']]
                differing_voterows.reset_index(drop=True, inplace=True)
                print("Differing vote Rows:")
                print(differing_voterows)
                await bot.send_dataframe_as_message(chat_id, differing_voterows)  # Send the DataFrame as messages
                
            else:
                print("No differing vote rows found.")


           
            differing_sn_order = merged_sn_place_df[merged_sn_place_df['sn_diff']]
            # Select and print only the relevant columns
            if not differing_sn_order.empty:
                # Assuming 'df' is your DataFrame
                differing_sn_order.to_csv('differing_sn_order.csv', index=False)
                chat_id = ELASTOS_SCANDINAVIA
                HTML(differing_sn_order.to_html(open('differing_sn_order.html', 'w')))
                #differing_sn_order = differing_sn_order[['nickname_new', 'nickname_old','order']]
                #differing_sn_order.reset_index(drop=True, inplace=True)
                print("Differing SN Rows:")
                print(differing_sn_order)
                #old_supernodes_keys = df_old['ownerpublickey'].tolist()

                #await bot.report_differing_sn_order(chat_id, differing_sn_order, old_supernodes_keys)

                await bot.report_differing_sn_order(chat_id, differing_sn_order)  # Send the DataFrame as messages

            else:
                print("No differing SN rows found.")

            

            # -----------------------------------------------------------
            
            # ------------------ blockchain stuck logic ------------------

            data = {
                "blockheight": blockheight,
                "blockheight_old": blockheight_old, 
                "status": 'status'
            }

            # Convert the dictionary to a JSON string
            #json_data = json.dumps(data)

            chat_id = ELASTOS_SN_NOTIFYER

            if timepolling * blockStuckCount > 1200 and blockStuckCount >= 0:
                print(f'no new block detected, block {blockheight} \n will report when new block mined.  ')
                # only repport once
                blockStuckCount = -1
                data["status"] = "stuck"
                json_data = json.dumps(data)
                await bot.report_blockchain_info(chat_id, json_data) 

            if  blockheight == blockheight_old and blockStuckCount >= 0:
                blockStuckCount = blockStuckCount+1
            elif not  blockheight == blockheight_old and blockStuckCount < 0:
                blockheight_old = blockheight
                blockStuckCount = 0
                print(f'not stuck anymore new block {blockheight}, old block {blockheight_old}')
                data["status"] = "unstuck"
                json_data = json.dumps(data)
                await bot.report_blockchain_info(chat_id, json_data) 
            elif not  blockheight == blockheight_old and blockStuckCount >= 0:
                blockheight_old = blockheight
                blockStuckCount = 0

            # -------------------------------------------------------------

            df_old=df.copy()

            print(f'new row sleep {timepolling}s')
            time.sleep(timepolling)
        else:
            
            if blockheight:
                blockheight_old = blockheight
            # If there was an error getting data, sleep and retry
            print(blockheight)
            print(f'fucked up or blockchain syncing trying again in few secs \nblockheight: {blockheight} \n')
            chat_id = ELASTOS_TESTCHANNEL  # Replace with the actual chat ID
            message = f'fucked up or blockchain syncing trying again in a minute \n blockheight: {blockheight} \n'
            await bot.post_message(message, chat_id)

            time.sleep(60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())