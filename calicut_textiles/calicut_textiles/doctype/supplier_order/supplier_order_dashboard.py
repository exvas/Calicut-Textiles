def get_data():
    return {
        'fieldname': 'supplier_order_id',  # Frappe will use this to find linked POs
        'transactions': [
            {
                'label': 'Linked Documents',
                'items': ['Purchase Order']
            }
        ]
    }
