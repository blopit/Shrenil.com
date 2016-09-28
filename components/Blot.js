var React = require('react');

var Blot = React.createClass({

    getInitialState(){

        return {
            rotation: 0,
            page: 'main'
        };
    },


    render(){

        return (

            <div className="circle">
                Circle


            </div>

        );
    }

});

module.exports = Blot;