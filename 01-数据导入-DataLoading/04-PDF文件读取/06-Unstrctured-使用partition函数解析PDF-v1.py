from unstructured.partition.auto import partition
# filename = "90-文档-Data/黑悟空/黑神话悟空.pdf"
filename = "90-文档-Data/山西文旅/云冈石窟-ch.pdf"

elements = partition(filename=filename, 
                     content_type="application/pdf"
                    )
print("\n\n".join([str(el) for el in elements][:10]))

