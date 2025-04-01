{
    'name':'shz_excell_commandes',
    'version':'17.0.1.0.0',
    'category':'',
    'summary':'',
    'author':'Mohamed Belaid',
    'depends': ['sale', 'stock', 'sale_management'],  # Doit inclure ces 3 modules
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_report_views.xml',
        'views/menu_views.xml'

             ],  # Doit pointer vers votre fichier XML
    'controllers':[

    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
