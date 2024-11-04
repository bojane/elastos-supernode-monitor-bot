import asyncio
import configparser
from telegram import Bot
import pandas as pd
import json

class TelegramBot:
    def __init__(self, config_file):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.token = self.config.get('Telegram', 'token')
        self.bot = Bot(token=self.token)

    async def post_message(self, message, chat_id):
        try:
            await self.bot.send_message(chat_id=chat_id, text=message)
            print("Message posted successfully!")
        except Exception as e:
            print(f"Failed to post message: {e}")

    async def get_chat_id(self, username):
        try:
            chat = await self.bot.get_chat(username)
            return chat.id
        except Exception as e:
            print(f"Failed to get chat ID: {e}")
            return None
        
    async def send_telegram_message(self, chat_id, message):
        try:
            await self.post_message(message, chat_id)
        except Exception as e:
            print(f"Failed to send message: {e}")

    async def send_dataframe_as_message(self, chat_id, dataframe):
        # Initialize the message
        threshold = 16000
        message = ""

        # Iterate through the rows of the DataFrame and concatenate the message
        for index, row in dataframe.iterrows():
            nickname_old = row["nickname_old"]
            dposv2votes_old = row["dposv2votes_old"]
            dposv2votes_new = row["dposv2votes_new"]
            dposv2votes_diff = row["dposv2votes_diff"]

            # Round the values to remove decimals
            dposv2votes_old = round(dposv2votes_old)
            dposv2votes_new = round(dposv2votes_new)
            dposv2votes_diff = round(dposv2votes_diff)
    
            if abs(dposv2votes_diff) > threshold:
                line = (
                    f"New votes on {nickname_old}:\nWent from {dposv2votes_old} to {dposv2votes_new}. "
                    f"Number of votes: {dposv2votes_diff}\n\n"
            )

                message += line
        if message:
            header = f'Only voting change above {threshold}.\n\n'
            message = header + message
             # Send the combined message as a single message
            await self.send_telegram_message(chat_id, message)
        else: 
            print("Not over thershold votes rows found.")

 
    
    async def report_differing_sn_order(self, chat_id, differing_sn_order, order_change_threshold=5):
        messages = []



        for index, row in differing_sn_order.iterrows():
            nickname_new = row["nickname_new"]
            nickname_old = row["nickname_old"]
            order = row["order"]
            voting = row['dposv2votes_new']
            ownerpublickey = row["ownerpublickey_new"]
            filtered_rows = differing_sn_order[differing_sn_order["ownerpublickey_old"] == ownerpublickey]

            if not filtered_rows.empty:  # Check if the filtered result is not empty
                

                previous_order = filtered_rows["order"].values[0]
                previous_voting = filtered_rows["dposv2votes_old"].values[0]
                
                # Calculate the change in order and voting
                order_change = abs(order - previous_order)

                if not voting == previous_voting and order_change >= order_change_threshold:
                    message = f"Change order of supernode:\n{nickname_new} went from place {previous_order} to {order}.\n"
                    messages.append(message)
            else:
                # This block now handles new supernodes
                message = f"New supernode detected: {nickname_new} now appears in the order at position {order}.\n"
                messages.append(message)

        if messages:
            header = f"Reporting order changes bigger than or equal to {order_change_threshold} positions.\n\n"
            #await self.send_telegram_message(chat_id, "\n".join(messages))
            await self.send_telegram_message(chat_id, header + "\n".join(messages))
        else:
            print("No differing SN order rows found.")
            


  

    async def report_differing_state(self, chat_id, differing_staterows):
        messages = []

        for index, row in differing_staterows.iterrows():
            nickname_old = row["nickname_old"]
            state_new = row["state_new"]
            state_old = row["state_old"]

            message = f"{nickname_old} has a change in state:\nIt was {state_old}\nNow it's {state_new}.\n"
            messages.append(message)

        if messages:
            await self.send_telegram_message(chat_id, "\n".join(messages))
        else:
            print("No differing state rows found.")
            
    
    async def report_new_supernodes(self, chat_id, new_supernodes):
        """
        Sends a notification for each new supernode detected.

        Parameters:
        - chat_id: The Telegram chat ID where the message will be sent.
        - new_supernodes: A DataFrame containing information about the new supernodes.
        """
        if new_supernodes.empty:
            print("No new supernodes detected. false detection in posting2py")
            return

        messages = []
        print(new_supernodes.head())  # Print the first few rows of the DataFrame
        print(new_supernodes.columns)  # Print the column names of the DataFrame
        for index, row in new_supernodes.iterrows():
            nickname_new = row.get("nickname_new")
            order = row.get("order")
            message = f"New supernode detected: {nickname_new}, now appears in the order at position {order}."
            messages.append(message)

        # Send messages if any new supernodes are detected
        if messages:
            notification_message = "\n".join(messages)
            await self.send_telegram_message(chat_id, notification_message)
        else:
            print("No new supernodes to report in posting2py")


    async def report_blockchain_info(self, chat_id, data ):
        
        data_dict = json.loads(data)

        # Access the values from the data dictionary
        blockheight = data_dict["blockheight"]
        blockheight_old = data_dict["blockheight_old"]
        status = data_dict["status"]

        message = ""

        if status == 'stuck':
            message = f"Houston! \nChain is stuck \nCurrent block is: \n{blockheight} \n"

        elif status == 'unstuck':
            message = f"Hurray! \nChain is unstuck \nCurrent block is: \n{blockheight} \nOld block: \n{blockheight_old} "
            

        if message:
            await self.send_telegram_message(chat_id, "\n".join(message))
        else:
            print("No status found, chain stuck or what?")


# Example usage:
if __name__ == "__main__":
    bot = TelegramBot("telegram.ini")
    message = "This is a test message."
    chat_id = -1001497151029  # Replace with the actual chat ID

    async def main():
        print("Before sending message")
        #await bot.post_message(message, chat_id)
        await bot.send_telegram_message(chat_id, "\n".join(message))
        print("After sending message")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())