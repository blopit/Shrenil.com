var React = require('react');

var Search = require('./Search');
var Map = require('./Map');
var CurrentLocation = require('./CurrentLocation');
var LocationList = require('./LocationList');


var App = React.createClass({

	getInitialState(){

		return {
			rotation: 0,
			page: 'main'
		};
	},


	render(){

		return (

			<div>
				<h1>Your Google Maps Locations</h1>


			</div>

		);
	}

});

module.exports = App;