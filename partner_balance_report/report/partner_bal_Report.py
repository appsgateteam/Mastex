from odoo import api, models, _
from odoo.exceptions import except_orm, ValidationError ,UserError


class PartnerBalReport(models.AbstractModel):
    _name = 'report.partner_balance_report.partner_balance_report_view'
    _description = 'Partner Balance Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        partner = data['form']['partner']
        # if data['form']['project']:
        #     appointments = self.env['hospital.appointment'].search([('patient_id', '=', data['form']['patient_id'][0])])
        # else:
        appointment_list = []
        array = []
        array2 = []
        array3 = []
        vals = {}
        # for rec in data['form']['project']:
        #     appointments = self.env['account.move.line'].search([('analytic_account_id','=',rec['id'])])
        #     for l in appointments:
        #         vals = {
        #             'debit':l.debit,
        #             'credit':l.credit,
        #         }
        #         array.append(vals)
        
        d_from = str(start_date)
        to = str(end_date)
        self.env.cr.execute("""select sum(init.debit) as init_dr,
                            sum(init.credit) as init_cr,
                            sum(init.balance) as init_bal,
                            --
                            sum(trn.debit) as trn_dr,
                            sum(trn.credit) as trn_cr,
                            sum(trn.balance) as trn_bal,
                            init.partner_id as partner_id
                        from account_move_line init, account_move_line trn
                        where init.account_internal_type in ('receivable','payable')
                            and init.parent_state='posted' 
                            and CAST(init.date as date) < '%s'
                            and init.partner_id=trn.partner_id
                            and trn.account_internal_type in ('receivable','payable')
                            and trn.parent_state='posted' 
                            and (CAST(trn.date as date) >= '%s' and CAST(trn.date as date) <= '%s')
                        group by init.partner_id"""% (d_from,d_from,to))
        # querys = self.env.cr.execute(query,)
        result = self.env.cr.dictfetchall()
        
        if  data['form']['partner']:
            for res in result:
                for rec in data['form']['partner']:
                    if rec['id'] == res['partner_id']:
                        vals = {
                            'init_dr':res['init_dr'],
                            'init_cr':res['init_cr'],
                            'init_bal':res['init_bal'],
                            'trn_dr':res['trn_dr'],
                            'trn_cr':res['trn_cr'],
                            'trn_bal':res['trn_bal'],
                        }
                        array3.append(vals)
        else:
            for res in result:
                # for rec in data['form']['partner']:
            
                vals = {
                    'init_dr':res['init_dr'],
                    'init_cr':res['init_cr'],
                    'init_bal':res['init_bal'],
                    'trn_dr':res['trn_dr'],
                    'trn_cr':res['trn_cr'],
                    'trn_bal':res['trn_bal'],
                }
                array3.append(vals)

                    
          
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'start_date': start_date,
            'end_date': end_date,
            # 'date_end': date_end,
            # 'sales_person': sales_person,
            'docs': array3,
            # 'total': array2,
        }
