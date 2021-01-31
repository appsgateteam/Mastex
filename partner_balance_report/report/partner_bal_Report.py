from odoo import api, models, _
from odoo.exceptions import except_orm, ValidationError ,UserError


class PartnerBalReport(models.AbstractModel):
    _name = 'report.partner_balance_report.partner_balance_report_view'
    _description = 'Partner Balance Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        type = data['form']['type']
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
        
        # d_from = '%s' %(start_date)
        # to = '%s' %(end_date)
        # raise UserError(to)
        if type == 'Payables Accounts':
            self.env.cr.execute("""select partner_id as partner_id,name as name, sum(init_debit) as init_debit, sum(init_credit) as init_credit, sum(init_balance) as init_balance, 
                                    sum(init_for) as init_for,sum(trn_for) as trn_for,sum(trn_debit) as trn_debit, sum(trn_credit) as trn_credit, sum(trn_balance) as trn_balance
                                from (
                                select a.partner_id partner_id,
                                sum(a.debit) init_debit,
                                sum(a.credit) init_credit,
                                sum(a.balance) init_balance,
                                sum(a.amount_currency) init_for,
                                sum(0) trn_for,
                                sum(0) trn_debit,
                                sum(0) trn_credit,
                                sum(0) trn_balance
                                from account_move_line a
                                where 
                                a.account_internal_type = 'payable'
                                and a.parent_state='posted'
                                and a.date < to_date('%s','yyyy-mm-dd')
                                group by a.partner_id
                                union
                                select
                                b.partner_id partner_id,
                                sum(0) init_debit,
                                sum(0) init_credit,
                                sum(0) init_balance,
                                sum(0) init_for,
                                sum(b.amount_currency) trn_for,
                                sum(b.debit) trn_debit,
                                sum(b.credit) trn_credit,
                                sum(b.balance) trn_balance
                                from account_move_line b
                                where	b.account_internal_type = 'payable'
                                and b.parent_state='posted'
                                and b.date between to_date('%s','yyyy-mm-dd') and to_date('%s','yyyy-mm-dd')
                                group by b.partner_id
                                ) all_tables , res_partner
                                where id=partner_id
                                group by partner_id, name
                                order by name"""%(start_date,start_date,end_date))
        elif type == 'Receivables Accounts':
            self.env.cr.execute("""select partner_id as partner_id,name as name, sum(init_debit) as init_debit, sum(init_credit) as init_credit, sum(init_balance) as init_balance, 
                                    sum(init_for) as init_for,sum(trn_for) as trn_for,sum(trn_debit) as trn_debit, sum(trn_credit) as trn_credit, sum(trn_balance) as trn_balance
                                from (
                                select a.partner_id partner_id,
                                sum(a.debit) init_debit,
                                sum(a.credit) init_credit,
                                sum(a.balance) init_balance,
                                sum(a.amount_currency) init_for,
                                sum(0) trn_for,
                                sum(0) trn_debit,
                                sum(0) trn_credit,
                                sum(0) trn_balance
                                from account_move_line a
                                where 
                                a.account_internal_type = 'receivable'
                                and a.parent_state='posted'
                                and a.date < to_date('%s','yyyy-mm-dd')
                                group by a.partner_id
                                union
                                select
                                b.partner_id partner_id,
                                sum(0) init_debit,
                                sum(0) init_credit,
                                sum(0) init_balance,
                                sum(0) init_for,
                                sum(b.amount_currency) trn_for,
                                sum(b.debit) trn_debit,
                                sum(b.credit) trn_credit,
                                sum(b.balance) trn_balance
                                from account_move_line b
                                where	b.account_internal_type = 'receivable'
                                and b.parent_state='posted'
                                and b.date between to_date('%s','yyyy-mm-dd') and to_date('%s','yyyy-mm-dd')
                                group by b.partner_id
                                ) all_tables , res_partner
                                where id=partner_id
                                group by partner_id, name
                                order by name"""%(start_date,start_date,end_date))
        else:
            self.env.cr.execute("""select partner_id as partner_id,name as name, sum(init_debit) as init_debit, sum(init_credit) as init_credit, sum(init_balance) as init_balance, 
                                    sum(init_for) as init_for,sum(trn_for) as trn_for,sum(trn_debit) as trn_debit, sum(trn_credit) as trn_credit, sum(trn_balance) as trn_balance
                                from (
                                select a.partner_id partner_id,
                                sum(a.debit) init_debit,
                                sum(a.credit) init_credit,
                                sum(a.balance) init_balance,
                                sum(a.amount_currency) init_for,
                                sum(0) trn_for,
                                sum(0) trn_debit,
                                sum(0) trn_credit,
                                sum(0) trn_balance
                                from account_move_line a
                                where 
                                a.account_internal_type in ('receivable','payable')
                                and a.parent_state='posted'
                                and a.date < to_date('%s','yyyy-mm-dd')
                                group by a.partner_id
                                union
                                select
                                b.partner_id partner_id,
                                sum(0) init_debit,
                                sum(0) init_credit,
                                sum(0) init_balance,
                                sum(0) init_for,
                                sum(b.amount_currency) trn_for,
                                sum(b.debit) trn_debit,
                                sum(b.credit) trn_credit,
                                sum(b.balance) trn_balance
                                from account_move_line b
                                where	b.account_internal_type in ('receivable','payable')
                                and b.parent_state='posted'
                                and b.date between to_date('%s','yyyy-mm-dd') and to_date('%s','yyyy-mm-dd')
                                group by b.partner_id
                                ) all_tables , res_partner
                                where id=partner_id
                                group by partner_id, name
                                order by name"""%(start_date,start_date,end_date))
        # querys = self.env.cr.execute(query,)
        result = self.env.cr.dictfetchall()

        # if data['form']['partner']:
        #     raise UserError("tesst")
        # else:
        # raise UserError(result)
        
        if data['form']['partner']:
            
            for rec in data['form']['partner']:
                for res in result:
                    # raise UserError("%s %s"%(res['partner_id'],rec['id']))
                    # if str(res['init_date']) <= str(end_date) and (str(res['tran_date']) >= str(start_date) and str(res['tran_date']) <= str(end_date)):
                    if rec['id'] == res['partner_id']:
                        vals = {
                            'init_dr':res['init_debit'],
                            'name':res['name'],
                            'init_cr':res['init_credit'],
                            'init_bal':res['init_balance'],
                            'trn_dr':res['trn_debit'],
                            'trn_cr':res['trn_credit'],
                            'trn_bal':res['trn_balance'],
                            'init_for':res['init_for'],
                            'trn_for':res['trn_for'],
                            'ending_for':res['init_for'] + res['trn_for'],
                            'Ending_dr':res['init_debit'] + res['trn_debit'],
                            'Ending_cr':res['init_credit'] + res['trn_credit'],
                            'Ending_bal':res['init_balance'] + res['trn_balance'],
                        }
                        array3.append(vals)
        else:
            for res in result:
                # for rec in data['form']['partner']:
                # if str(res['init_date']) <= str(end_date) and (str(res['tran_date']) >= str(start_date) and str(res['tran_date']) <= str(end_date)):
                vals = {
                    'init_dr':res['init_debit'],
                    'name':res['name'],
                    'init_cr':res['init_credit'],
                    'init_bal':res['init_balance'],
                    'trn_dr':res['trn_debit'],
                    'trn_cr':res['trn_credit'],
                    'trn_bal':res['trn_balance'],
                    'init_for':res['init_for'],
                    'trn_for':res['trn_for'],
                    'ending_for':res['init_for'] + res['trn_for'],
                    'Ending_dr':res['init_debit'] + res['trn_debit'],
                    'Ending_cr':res['init_credit'] + res['trn_credit'],
                    'Ending_bal':res['init_balance'] + res['trn_balance'],
                }
                array3.append(vals)

                    
          
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'start_date': start_date,
            'end_date': end_date,
            'type': type,
            # 'date_end': date_end,
            # 'sales_person': sales_person,
            'docs': array3,
            # 'total': array2,
        }
