from flask import Blueprint, jsonify
from database.data_access import get_statistics


statistics_api = Blueprint('statistics_api', __name__, url_prefix='/api')


@statistics_api.route('/statistics', methods=['GET'])
def statistics():
	return jsonify(get_statistics())


