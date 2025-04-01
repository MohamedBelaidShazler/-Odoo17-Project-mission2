# -*- coding: utf-8 -*-
from odoo import models, fields, api
import io
import xlsxwriter
from datetime import datetime
import base64


class SaleOrderReportWizard(models.TransientModel):
    _name = 'sale.order.report.wizard'
    _description = 'Wizard pour générer le rapport des commandes avec livraisons'

    date_start = fields.Date(string='Date de début', required=True)
    date_end = fields.Date(string='Date de fin', required=True)
    excel_file = fields.Binary(string='Fichier Excel')
    filename = fields.Char(string='Nom du fichier')

    def generate_excel_report(self):
        # Récupérer les données
        sale_orders = self._get_sale_orders()

        # Créer le fichier Excel
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Rapport Commandes')


        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#FFFFCC',
            'border': 1,
            'align': 'center'
        })
        title_format = workbook.add_format({'bold': True, 'font_size': 14})
        command_row_format = workbook.add_format({'bg_color': '#E6E6FA', 'border': 1})
        delivery_row_format = workbook.add_format({'border': 1})

        # En-tête du rapport
        worksheet.merge_range('A1:I1', 'Rapport des Commandes avec Livraisons', title_format)
        worksheet.write('A2', f"Période : {self.date_start} au {self.date_end}")
        worksheet.write('A3', f"Généré par : {self.env.user.name}")
        worksheet.write('A4', f"Date de génération : {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # En-têtes de colonnes
        headers = [
            'Réf. Commande', 'Date', 'Client', 'Montant Total',
            'Statut', 'Quantité Restante à Livrer',
            'Réf. BL', 'Article', 'Qté Livrée'
        ]
        for col, header in enumerate(headers):
            worksheet.write(5, col, header, header_format)

        row = 6  # Ligne de départ des données

        for order in sale_orders:
            # Calculer la quantité restante à livrer
            qty_delivered = sum(
                move.quantity if hasattr(move, 'quantity') else move.quantity_done
                for picking in order.picking_ids.filtered(lambda p: p.state == 'done')
                for move in picking.move_ids.filtered(lambda m: m.product_id.type in ['product'])
            )
            qty_ordered = sum(line.product_uom_qty for line in order.order_line)
            qty_remaining = qty_ordered - qty_delivered

            # Ligne principale de la commande
            worksheet.write(row, 0, order.name, command_row_format)
            worksheet.write(row, 1, order.date_order.strftime('%d/%m/%Y'), command_row_format)
            worksheet.write(row, 2, order.partner_id.name, command_row_format)
            worksheet.write(row, 3, order.amount_total, command_row_format)
            worksheet.write(row, 4, "Confirmée & LB", command_row_format)
            worksheet.write(row, 5, qty_remaining if qty_remaining > 0 else 0, command_row_format)
            # Colonnes BL vides pour la ligne commande
            worksheet.write_blank(row, 6, None, command_row_format)
            worksheet.write_blank(row, 7, None, command_row_format)
            worksheet.write_blank(row, 8, None, command_row_format)

            row += 1

            # Lignes des livraisons
            for picking in order.picking_ids.filtered(lambda p: p.state == 'done'):
                for move in picking.move_ids.filtered(lambda m: m.product_id.type in ['product']):
                    qty_done = move.quantity if hasattr(move, 'quantity') else move.quantity_done
                    if qty_done > 0:
                        # Ligne de livraison
                        worksheet.write_blank(row, 0, None, delivery_row_format)
                        worksheet.write_blank(row, 1, None, delivery_row_format)
                        worksheet.write_blank(row, 2, None, delivery_row_format)
                        worksheet.write_blank(row, 3, None, delivery_row_format)
                        worksheet.write(row, 4, "BL Livré", delivery_row_format)
                        worksheet.write_blank(row, 5, None, delivery_row_format)
                        worksheet.write(row, 6, picking.name, delivery_row_format)
                        worksheet.write(row, 7, move.product_id.name, delivery_row_format)
                        worksheet.write(row, 8, qty_done, delivery_row_format)

                        row += 1


        col_widths = {
            'A': 15, 'B': 10, 'C': 25,
            'D': 12, 'E': 15, 'F': 20,
            'G': 15, 'H': 25, 'I': 10
        }
        for col, width in col_widths.items():
            worksheet.set_column(f'{col}:{col}', width)

        workbook.close()
        output.seek(0)

        # Générer le fichier
        filename = f"rapport_commandes_livraisons_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        self.write({
            'excel_file': base64.b64encode(output.getvalue()),
            'filename': filename
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/excel_file/{filename}?download=true',
            'target': 'self',
        }

    def _get_sale_orders(self):
        return self.env['sale.order'].search([
            ('state', '=', 'sale'),  # Commandes confirmées
            ('date_order', '>=', self.date_start),
            ('date_order', '<=', self.date_end),
            ('picking_ids.state', '=', 'done'),  # Avec au moins une livraison effectuée
            ('order_line.product_id.type', 'in', ['product'])  # Produits stockables
        ], order='date_order asc')