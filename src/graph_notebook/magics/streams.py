import re
import json
import urllib.request
import urllib.error
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output

class EventId:
    def __init__(self, commit_num=1, op_num=1):
        self.commit_num = commit_num
        self.op_num = op_num
    
    def update(self, event_id):
        if event_id is not None:
            self.commit_num = event_id.commit_num
            self.op_num = event_id.op_num
        
class StreamViewer:
    
    def __init__(self,uri_with_port,language):
        self.uri_with_port = uri_with_port
        self.language = language
        self.last_event_id = EventId()
        self.dropdown = widgets.Dropdown(options=['gremlin', 'sparql'], value=language, disabled=False)
        self.dropdown.layout.width = '10%'
        self.dropdown.observe(self.on_dropdown_changed)
        self.slider = widgets.IntSlider(continuous_update=False, readout=False)
        self.next_button = widgets.Button(description='Next', tooltip='Next')
        self.next_button.layout.width = '10%'
        self.next_button.on_click(self.on_next)
        self.ui = widgets.HBox([self.slider, self.next_button, self.dropdown])
        self.out = widgets.interactive_output(self.on_slider_changed, {'commit_num': self.slider})

    def stream_uri(self):
        self.language = self.dropdown.value
        uri = f'{self.uri_with_port}/{self.language.lower()}/stream/'
        #TODO: Remove print before PR
        print(uri)
        return uri
    
    def get_events(self, commit_num, op_num, iterator):
        try:
            req = urllib.request.Request('{}?iteratorType={}&commitNum={}&opNum={}'.format(self.stream_uri(), iterator, commit_num, op_num))
            response = urllib.request.urlopen(req)
            jsonresponse = json.loads(response.read().decode('utf8'))
            
            records = jsonresponse['records']
            first_event = EventId(records[0]['eventId']['commitNum'], records[0]['eventId']['opNum'])
            last_event = EventId(jsonresponse['lastEventId']['commitNum'], jsonresponse['lastEventId']['opNum'])
            
            return (records, first_event, last_event)
        except urllib.error.HTTPError as e:
            return ([], None, None)
    
    def show_records(self, records):
        
        html = '''<table style="border: 1px solid black">'''
        
        commit_num = None
 
        for record in records:
            current_commit_num = record['eventId']['commitNum']
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
                record['data'])
           
        html += '</table></body></html>'
        display(HTML(html))
        
    def parse_last_commit_num(self, msg):
        results = re.findall("\d+", msg)      
        return None if not results else results[0]
    
    def get_last_commit_num(self):
           
        commit_num = 1000000000
        
        while True:
            try:
                req = urllib.request.Request('{}?commitNum={}&limit=1'.format(self.stream_uri(), commit_num))
                response = urllib.request.urlopen(req)
                jsonresponse = json.loads(response.read().decode('utf8'))
                
                commit_num = commit_num + 1000000000
                
            except urllib.error.HTTPError as e:
                
                msg = json.loads(e.read().decode('utf8'))['detailedMessage']
                return self.parse_last_commit_num(msg)
            
    def get_first_commit_num(self):
           
        try:
            req = urllib.request.Request('{}?iteratorType=TRIM_HORIZON&limit=1'.format(self.stream_uri()))
            response = urllib.request.urlopen(req)
            jsonresponse = json.loads(response.read().decode('utf8'))
        
            return jsonresponse['lastEventId']['commitNum']
        
        except urllib.error.HTTPError as e:
            return None
            
    def refresh(self, commit_num, op_num, iterator):
        
        (records, first_event, last_event) = self.get_events(commit_num, op_num, iterator)
        self.show_records(records)
        
        self.last_event_id.update(last_event)
        self.update_slider_min_max()
        
        
    def update_slider_min_max(self):
        last = self.get_last_commit_num()
        first = self.get_first_commit_num()
        #TODO: Remove print before PR
        print(f'First={first}  Last={last}')
        
        if last is None and first is None:
            self.slider.min = 0
            self.slider.max = 0
        else:
            self.slider.max = last
            self.slider.min = first
        
          
    def on_slider_changed(self, commit_num):
        if commit_num == self.last_event_id.commit_num:
            self.refresh(commit_num, self.last_event_id.op_num, 'AFTER_SEQUENCE_NUMBER')
        else:
            self.refresh(commit_num, 1, 'AT_SEQUENCE_NUMBER')
    
    def on_next(self, _):
        self.slider.value = self.last_event_id.commit_num
        
    def on_dropdown_changed(self, changes):
        self.update_slider_min_max()
        if self.slider.min == self.slider.max == 0:
            self.out.clear_output()
  
    def show(self):
        self.update_slider_min_max()
        display(self.ui, self.out)
