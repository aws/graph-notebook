import re
import json
import urllib.request
import urllib.error
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
from graph_notebook.neptune.client import STREAM_AT, STREAM_AFTER, STREAM_TRIM, STREAM_EXCEPTION_NOT_FOUND
class EventId:
    def __init__(self, commit_num=1, op_num=1):
        self.commit_num = int(commit_num)
        self.op_num = int(op_num)
        self.nudge = True
    
    def update(self, event_id):
        if event_id is not None:
            if event_id.commit_num != self.commit_num:
                self.nudge = True
            self.commit_num = event_id.commit_num
            self.op_num = event_id.op_num

class StreamClient:
    
    def __init__(self, wb_client, uri_with_port):
        self.wb_client = wb_client
        self.uri_with_port = uri_with_port
    
    
    def get_events(self, language, event_id, iterator):
        try:
            #url = '{}?iteratorType={}&commitNum={}&opNum={}'.format(self.__stream_uri(language), iterator, event_id.commit_num, event_id.op_num)
            #
            #req = urllib.request.Request(url)
            #response = urllib.request.urlopen(req)
            #jsonpayload = response.read().decode('utf8')
            jsonresponse = self.wb_client.stream(self.__stream_uri(language),
                                                 iteratorType = iterator,
                                                 commitNum = event_id.commit_num,
                                                 opNum = event_id.op_num)
                                                 
            if 'records' in jsonresponse:
                records = jsonresponse['records']
                first_event = EventId(records[0]['eventId']['commitNum'], records[0]['eventId']['opNum'])
                last_event = EventId(jsonresponse['lastEventId']['commitNum'], jsonresponse['lastEventId']['opNum'])
                
                return (records, first_event, last_event)
            else:
                return ([], None, None)
                
        #except urllib.error.HTTPError as e:
        except:
            return ([], None, None)
        
    def __parse_last_commit_num(self, msg):
        results = re.findall("\d+", msg)      
        return None if not results else results[0]
    
    def __stream_uri(self, language):
        uri = f'{self.uri_with_port}/{language.lower()}/stream/'
        return uri
    
    # TODO: Revisit this logic if the Neptune Stream API adds support for querying this
    # directly.
    def get_last_commit_num(self, language):
           
        commit_num = 1000000000
        
        while True:
            #try:
                #req = urllib.request.Request('{}?commitNum={}&limit=1'.format(self.__stream_uri(language), commit_num))
                #response = urllib.request.urlopen(req)
                #jsonresponse = json.loads(response.read().decode('utf8'))
            jsonresponse = self.wb_client.stream(self.__stream_uri(language),
                                                 commitNum = commit_num,
                                                 limit = 1)
                
            commit_num = commit_num + 1000000000
                
            #except urllib.error.HTTPError as e:
            if  jsonresponse['code'] == STREAM_EXCEPTION_NOT_FOUND:    
                msg = jsonresponse['detailedMessage']
                return self.__parse_last_commit_num(msg)
            
    def get_first_commit_num(self, language):
        try:
            #req = urllib.request.Request('{}?iteratorType=TRIM_HORIZON&limit=1'.format(self.__stream_uri(language)))
            #response = urllib.request.urlopen(req)
            #jsonresponse = json.loads(response.read().decode('utf8'))
            jsonresponse = self.wb_client.stream(self.__stream_uri(language),
                                                 iteratorType = STREAM_TRIM,
                                                 limit = 1)
            c = jsonresponse['lastEventId']['commitNum']
            return c
        #except urllib.error.HTTPError as e:
        except:
            return None

class StreamViewer:
    
    def __init__(self, wb_client, uri_with_port, language):
        self.stream_client = StreamClient(wb_client, uri_with_port)
        self.last_displayed_event_id = EventId()
        self.slider = widgets.FloatSlider(continuous_update=False, readout=False, step=1.0)
        self.slider.observe(self.on_slider_changed)
        self.next_button = widgets.Button(description='Next', tooltip='Next')
        self.next_button.layout.width = '10%'
        self.next_button.on_click(self.on_next)
        self.dropdown = widgets.Dropdown(options=['gremlin', 'sparql'], value=language, disabled=False)
        self.dropdown.layout.width = '10%'
        self.dropdown.observe(self.on_dropdown_changed)
        self.out = widgets.Output()
        self.ui = widgets.HBox([self.slider, self.next_button, self.dropdown])
        
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
                self.update_slider_min_max_values(language)
                self.slider.value = self.last_displayed_event_id.commit_num
                self.show_records(records)
                self.last_displayed_event_id.update(last_event)
            
    def init_display(self, language):
        self.update_slider_min_max_values(language)
        self.slider.value = self.slider.min
        (records, first_event, last_event) = self.stream_client.get_events(language, EventId(self.slider.min, 1), STREAM_AT)
        self.show_records(records)
        self.last_displayed_event_id.update(last_event)
       

    def show_records(self, records):
        
        html = '''<html><body><table style="border: 1px solid black">'''
            
        commit_num = None
     
        for record in records:
            current_commit_num = record['eventId']['commitNum']
            
            data = json.dumps(record['data']).replace('&', '&amp;').replace('<', '&lt;')
            
            if commit_num is None or current_commit_num != commit_num:
                commit_num = current_commit_num
                html += '<tr style="border: 1px solid black; background-color: gainsboro ; font-weight: bold;">'
                html += '<td style="border: 1px solid black; vertical-align: top; text-align: left;" colspan="3">{}</td>'.format(commit_num)
                html += '</tr><tr style="border: 1px solid black;">'     
            
            html += '<tr style="border: 1px solid black; background-color: white;">'
            html += '''<td style="border: 1px solid black; vertical-align: top;">{}</td>
            <td style="border: 1px solid black; vertical-align: top;">{}</td>
            <td style="border: 1px solid black; vertical-align: top; text-align: left;">{}</td></tr>'''.format(
                record['eventId']['opNum'], 
                record['op'],
                data)
           
        html += '</table></body></html>'
        
        self.out.clear_output(wait=True)
        with self.out:
            display(HTML(html))
            
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
       
