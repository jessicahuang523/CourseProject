import sqlite3
import pandas as pd 
db_name = 'TMS'


def read_sql(doc_name,tbl_name,col_name):
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cmd = "SELECT * from " +  tbl_name 
        cur.execute(cmd+" where docid LIKE (?) order by CAST(ts as REAL) asc",[doc_name+'%'])
        results = {}
        desc = cur.description
        column_names = [col[0] for col in desc]

        for row in cur.fetchall():
                id_ = ''
                val = ''
                for idx,c in enumerate(row):
                    if column_names[idx] == 'docid':
                        id_ = c 


                    elif column_names[idx] == col_name:

                        val = c 

               
                results[id_] = val 
        # print(results)
        con.commit()
        con.close()
        return results

def main():
    doc_name = 'judel_young'
    notes = read_sql(doc_name,'NOTE','note')
    rel = read_sql(doc_name,'RELEVANCE','rel')
    lst = []
    for k,v in rel.items():

        try:
           n = notes[k]
        except:
            n = ''
        lst.append([k,v,n])
    df = pd.DataFrame(lst)
    df.to_excel('judel_results.xlsx')

if __name__ == '__main__':
    main()
