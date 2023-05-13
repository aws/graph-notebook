import re
import json
import ipywidgets as widgets
import queue
from datetime import datetime
from IPython.display import display, HTML
from graph_notebook.neptune.client import STREAM_AT, STREAM_AFTER, STREAM_TRIM, STREAM_EXCEPTION_NOT_FOUND,\
                                          STREAM_EXCEPTION_NOT_ENABLED, STREAM_PG, STREAM_RDF, STREAM_ENDPOINTS,\
                                          STREAM_COMMIT_TIMESTAMP, STREAM_IS_LASTOP


class EventId:
    def __init__(self, commit_num=1, op_num=1):
        self.commit_num = int(commit_num)
        self.op_num = int(op_num)
        
    def update(self, event_id):
        if event_id is not None:
            self.commit_num = event_id.commit_num
            self.op_num = event_id.op_num
            
    def duplicate(self):
        return EventId(self.commit_num, self.op_num)

    def value(self):
        return '{}/{}'.format(self.commit_num, self.op_num)


class StreamClient:
    def __init__(self, wb_client, uri_with_port, limit=10):
        self.wb_client = wb_client
        self.uri_with_port = uri_with_port
        self.limit=limit
    
    def get_events(self, language, event_id, iterator):
        try:  
            jsonresponse = self.wb_client.stream(self.__stream_uri(language),
                                                 iteratorType = iterator,
                                                 commitNum = event_id.commit_num,
                                                 opNum = event_id.op_num,
                                                 limit=self.limit)
            if 'records' in jsonresponse:
                records = jsonresponse['records']
                first_event = EventId(records[0]['eventId']['commitNum'], records[0]['eventId']['opNum'])
                last_event = EventId(jsonresponse['lastEventId']['commitNum'], jsonresponse['lastEventId']['opNum'])

                return records, first_event, last_event
            else:
                return [], None, None
                
        except:
            return [], None, None
        
    def __parse_last_commit_num(self, msg):
        results = re.findall("\d+", msg)      
        return None if not results else results[0]
    
    def __stream_uri(self, language):
        uri = f'{self.uri_with_port}/{language.lower()}/stream/'
        return uri
    
    # TODO: Revisit this logic if the Neptune Stream API adds support for querying this
    # directly.
    def get_last_commit_num(self, language):
        # Using an explicit value rather than sys.maxsize as that can vary.
        commit_num = 2**63-1
        
        jsonresponse = self.wb_client.stream(self.__stream_uri(language),
                                             commitNum = commit_num,
                                             limit = 1)
            
        if jsonresponse['code'] == STREAM_EXCEPTION_NOT_FOUND:
            msg = jsonresponse['detailedMessage']
            return self.__parse_last_commit_num(msg)
        elif jsonresponse['code'] == STREAM_EXCEPTION_NOT_ENABLED:
            print('The stream is not enabled on this cluster')
            return None
            
    def get_first_commit_num(self, language):
        try:
            jsonresponse = self.wb_client.stream(self.__stream_uri(language),
                                                 iteratorType = STREAM_TRIM,
                                                 limit = 1)
            c = jsonresponse['lastEventId']['commitNum']
            return c
        except:
            return None


class StreamViewer:
    
    def __init__(self, wb_client, uri_with_port, language, limit=10):
        self.stream_client = StreamClient(wb_client, uri_with_port, limit=limit)
        self.first_displayed_event_id = EventId()
        self.last_displayed_event_id = EventId()
        self.history = None
        self.slider = widgets.FloatSlider(continuous_update=False, readout=False, step=1.0)
        self.slider.observe(self.on_slider_changed)
        self.next_button = widgets.Button(description='Next', tooltip='Next')
        self.next_button.layout.width = '10%'
        self.next_button.on_click(self.on_next)
        self.back_button = widgets.Button(description='Back', tooltip='Back', disabled=True)
        self.back_button.layout.width = '10%'
        self.back_button.on_click(self.on_back)
        self.dropdown = widgets.Dropdown(options=[STREAM_PG, STREAM_RDF], value=language, disabled=False)
        self.dropdown.layout.width = '15%'
        self.dropdown.observe(self.on_dropdown_changed)
        self.out = widgets.Output()
        self.ui = widgets.HBox([self.slider, self.back_button, self.next_button, self.dropdown])
        
    def show(self):
        language = self.dropdown.value
        display(self.ui, self.out)
        self.init_display(language)
     
    # Only when the slider is manipulated, fetch the relevant stream contents.
    # This method will not make updates if the slider was changed elsewhere by
    # our code. This avoids unnecessary processing.
    def on_slider_changed(self, changes):
        if changes['name'] == '_property_lock' and changes['new']:
            new_value = changes['new']['value'] 
            self.update_slider_min_max_values(self.dropdown.value)
            (records, first_event, last_event) = self.stream_client.get_events(self.dropdown.value, EventId(new_value, 1), STREAM_AT)
            self.show_records(records)
            self.first_displayed_event_id.update(first_event)
            self.last_displayed_event_id.update(last_event)   
            
    def on_dropdown_changed(self, changes):
        if changes['name'] == 'value':
            language = changes['new']
            self.init_display(language)

    def on_next(self, _):
        if self.last_displayed_event_id.commit_num <= self.slider.max:
            language = self.dropdown.value
            (records, first_event, last_event) = self.stream_client.get_events(language, self.last_displayed_event_id, STREAM_AFTER)
            if records:
                self.history.put(self.first_displayed_event_id.duplicate())
                self.back_button.disabled = False
                self.update_slider_min_max_values(language)
                self.slider.value = first_event.commit_num
                self.show_records(records)
                self.first_displayed_event_id.update(first_event)
                self.last_displayed_event_id.update(last_event)
                
    def on_back(self, _):
        if self.history.empty():
            return
        
        event_id = self.history.get()

        if self.history.empty():
            self.back_button.disabled = True
        
        if event_id:
            language = self.dropdown.value
            (records, first_event, last_event) = self.stream_client.get_events(language, event_id, STREAM_AT)
            self.update_slider_min_max_values(language)
            self.slider.value = first_event.commit_num
            self.show_records(records)
            self.first_displayed_event_id.update(first_event)
            self.last_displayed_event_id.update(last_event)
            
    def init_display(self, language):
        # Map the selected stream type to the actual endpoint name
        language = STREAM_ENDPOINTS[language] 
        self.history = queue.LifoQueue(100)
        self.back_button.disabled = True
        self.update_slider_min_max_values(language)
        self.slider.value = self.slider.min
        (records, first_event, last_event) = self.stream_client.get_events(language, EventId(self.slider.min, 1), STREAM_AT)
        self.show_records(records)
        self.first_displayed_event_id.update(first_event)
        self.last_displayed_event_id.update(last_event)
       
    def show_records(self, records):
        if len(records) > 0:
            html = '''<html><body><table style="border: 1px solid black">'''
            
            html += '''<tr>
                       <th style="text-align: center" title="The transaction or op number within a transaction">Tx/Op#</th>
                       <th style="text-align: center" title="The type of operation such as ADD or REMOVE">Operation</th>
                       <th style="text-align: center" title="Indicates if this is the final Op of a transaction. This feature requires a Neptune engine version of 1.1.1.0 or higher.">LastOp</th>
                       <th style="text-align: center;">Data</th>
                       </tr>'''
                
            commit_num = None
         
            for record in records:
                current_commit_num = record['eventId']['commitNum']
                timestamp = None
                lastop = False
                lastop_text = ''
                if STREAM_COMMIT_TIMESTAMP in record:
                    timestamp = record[STREAM_COMMIT_TIMESTAMP]
                    utc_text = datetime.utcfromtimestamp(timestamp/1000)

                data = json.dumps(record['data']).replace('&', '&amp;').replace('<', '&lt;')
                
                if commit_num is None or current_commit_num != commit_num:
                    commit_num = current_commit_num
                    html += '<tr style="border: 1px solid black; background-color: gainsboro ; font-weight: bold;">'
                    html += '<td title="The commit number for this transaction" style="border: 1px solid black; vertical-align: top; text-align: left;" colspan="4">{}'.format(commit_num)
                    if timestamp != None:
                        html += '&nbsp;&nbsp;&nbsp;Timestamp = {}'.format(timestamp)
                        html += '&nbsp;&nbsp;&nbsp;( {} UTC )'.format(utc_text)
                    html += '</td>'
                    html += '</tr><tr style="border: 1px solid black;">'     
                
                if STREAM_IS_LASTOP in record:
                    lastop = record[STREAM_IS_LASTOP]
                if lastop:
                    lastop_text = 'Y'

                html += '<tr  style="border: 1px solid black; background-color: white;">'
                html += '''<td  title="The operation number within this transaction" style="border: 1px solid black; vertical-align: top;">{}</td>
                <td  title="The operation performed"style="border: 1px solid black; vertical-align: top;text-align: center;">{}</td>
                <td  title="A Y indicates the final Op for a transaction. Earlier Neptune versions do not support this option." style="border: 1px solid black; vertical-align: top;text-align: center;">{}</td>
                <td  title="Details of the change made by this operation" style="border: 1px solid black; vertical-align: top; text-align: left;">{}</td></tr>'''.format(
                    record['eventId']['opNum'], 
                    record['op'],
                    lastop_text,
                    data)
               
            html += '</table></body></html>'
            
            self.out.clear_output(wait=True)
            with self.out:
                display(HTML(html))
        else:
            self.out.clear_output(wait=True)
            with self.out:
                display(HTML('<b>No records found to display</b>'))
            
    def update_slider_min_max_values(self, language):
        new_min = self.stream_client.get_first_commit_num(language)
        new_max = self.stream_client.get_last_commit_num(language)
        if new_min is None and new_max is None:
            self.slider.min = 0
            self.slider.max = 0
        elif float(new_max) < self.slider.min:
            self.slider.min = new_min
            self.slider.max = new_max               
        else:
            self.slider.max = new_max
            self.slider.min = new_min       
