from flask import Flask, render_template,request
import plotly
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
import json
from flask import * 
import os

app = Flask(__name__)
app.config['UPLOADED_PATH'] = os.path.join(app.root_path, 'upload')


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        for f in request.files.getlist('file'):
            f.save(os.path.join(app.config['UPLOADED_PATH'], f.filename))
    return render_template('index.html')

@app.route('/sensor')
def index():
    feature = 'Sensor'
    bar = create_plot(feature)
    return render_template('index.html', plot=bar)


def create_plot(feature):

    if feature == 'Concurrent_R1':    
        df=pd.read_csv('upload/sample.csv')
        set_num=df['parent']
        act=df['activity']
        time=df['time']
        date=df['date']

        data=px.tree(df,
                    path=[date,set_num,act],
                    values=time,height=800,
                    color_continuous_scale=['red','yellow','green']
                    )
        data.update_layout(
            title_font_size=42,
            title_font_family='Arial')
    
    elif feature == 'Concurrent_R2':
        df=pd.read_csv('upload/r2_con_date.csv')
        set_num=df['parent']
        act=df['activity']
        time=df['time']
        date=df['date']

        data=px.sunburst(df,
                    path=[date,set_num,act],
                    values=time,height=800,
                    color_continuous_scale=['red','yellow','green']
                    )
        data.update_layout(
            title_font_size=42,
            title_font_family='Arial')


    elif feature == 'Sensor':
        df = pd.read_csv('upload/sensor_data.csv')
        data = px.bar_polar(df, r="frequency", theta="sensor",
                        color="activity", height=800,
                        color_discrete_sequence= px.colors.sequential.Plasma_r)
        # fig.show()


    

    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON

@app.route('/bar', methods=['GET', 'POST'])
def change_features():

    feature = request.args['selected']
    graphJSON= create_plot(feature)




    return graphJSON

if __name__ == '__main__':
    app.run()
