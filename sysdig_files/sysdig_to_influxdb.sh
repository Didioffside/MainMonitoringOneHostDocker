#!/bin/sh

# InfluxDB configuration
INFLUXDB_URL="http://10.0.2.7:5007"
INFLUXDB_TOKEN="InfluxDBToken"
INFLUXDB_ORG="MyOrg"
INFLUXDB_BUCKET="Sysdig"

# Buffer configuration
BUFFER_SIZE=10000
MAX_BUFFER_TIME=60  # Maximum buffer time in seconds (adjust as needed)
event_buffer=()

# Function to flush the buffer to InfluxDB
flush_buffer() {
  if [ ${#event_buffer[@]} -gt 0 ]; then
    echo "Flushing ${#event_buffer[@]} events to InfluxDB $timestamp"

    # Prepare payload for InfluxDB
    payload=""
    for event in "${event_buffer[@]}"; do
      payload+="events,$event\n"
    done

    # Send the payload to InfluxDB using curl
    curl -X POST "$INFLUXDB_URL/api/v2/write?org=$INFLUXDB_ORG&bucket=$INFLUXDB_BUCKET&precision=s" \
      -H "Authorization: Token $INFLUXDB_TOKEN" \
      -H "Content-Type: text/plain; charset=utf-8" \
      --data-binary "$event_buffer"

    # Clear the buffer after flushing
    event_buffer=()
  fi
}




#LATEST VERSION WITHOUT BUFFERING
# Read Sysdig output line by line
while IFS=, read -r event_num timestamp event_cpu proc_name thread_tid event_dir event_type event_args
do
  # Prepare tags and fields, ensuring proper escaping and formatting
  tags="proc_name=\"$proc_name\",event_type=\"$event_type\""
  fields="event_num=$event_num,event_cpu=$event_cpu,thread_tid=\"$thread_tid\",event_dir=\"$event_dir\",event_args=\"$event_args\""

  # Convert timestamp to Unix timestamp format (seconds since epoch)
  unix_timestamp=$(date -d "$timestamp" +%s)
  #echo "$unix_timestamp"
  event="events,$tags $fields $unix_timestamp"
  event_buffer+=("$event")
  if [ ${#event_buffer[@]} -ge $BUFFER_SIZE ]; then
    flush_buffer
  fi
done
flush_buffer
  # Send the event data to InfluxDB using curl
#  curl -X POST "$INFLUXDB_URL/api/v2/write?org=$INFLUXDB_ORG&bucket=$INFLUXDB_BUCKET&precision=s" \
#    -H "Authorization: Token $INFLUXDB_TOKEN" \
#    -H "Content-Type: text/plain; charset=utf-8" \
#    --data-binary "events,$tags $fields $unix_timestamp"
#done




# Read Sysdig output line by line
#%evt.num,%evt.time,%evt.cpu,%proc.name,(%thread.tid),%evt.dir,%evt.type,%evt.args
#while IFS=, read -r event_num timestamp event_cpu proc_name thread_tid event_dir event_type event_args
#do
 # echo "Event: event_num=$event_num, timestamp=$timestamp, event_cpu=$event_cpu, proc_name=$proc_name, thread_tid=$thread_tid, event_dir=$event_dir, event_type=$event_type, event_args=$event_args"
#done



# Read Sysdig output line by line
#while IFS=, read -r timestamp event_type event_args
#do
  # Prepare the event data
#  event_data="event_type=$event_type,$event_args"
  
  # Send the event data to InfluxDB using curl
 # curl -X POST "$INFLUXDB_URL/api/v2/write?org=$INFLUXDB_ORG&bucket=$INFLUXDB_BUCKET&precision=s" \
  #  -H "Authorization: Token $INFLUXDB_TOKEN" \
   # --data-binary "sysdig_events $event_data $timestamp"
#done


