(docarray-serialization)=
# Serialization

DocArray is designed to be "ready-to-wire" at anytime. Serialization is important. DocumentArray provides multiple serialization methods that allows one transfer DocumentArray object over network and across different microservices.

- JSON string: `.from_json()`/`.to_json()` 
- Bytes (compressed): `.from_bytes()`/`.to_bytes()` 
- Protobuf Message: `.from_protobuf()`/`.to_protobuf()`
- Python List: `.from_list()`/`.to_list()`
- Pandas Dataframe: `.from_dataframe()`/`.to_dataframe()`
- Cloud: `.push()`/`.pull()`

## From/to JSON

```{important}
This feature requires `protobuf` dependency. You can do `pip install "docarray[full]"` to install it.
```

```python
from docarray import DocumentArray, Document

da = DocumentArray([Document(text='hello'), Document(text='world')])
da.to_json()
```

```text
[{"id": "72db9a7e6e3211ec97f51e008a366d49", "text": "hello", "mime_type": "text/plain"}, {"id": "72db9cb86e3211ec97f51e008a366d49", "text": "world", "mime_type": "text/plain"}]
```


```python
da_r = DocumentArray.from_json(da.to_json())

da_r.summary()
```

```text
                  Documents Summary                   
                                                      
  Length                 2                            
  Homogenous Documents   True                         
  Common Attributes      ('id', 'mime_type', 'text')  
                                                      
                     Attributes Summary                     
                                                            
  Attribute   Data type   #Unique values   Has empty value  
 ────────────────────────────────────────────────────────── 
  id          ('str',)    2                False            
  mime_type   ('str',)    1                False            
  text        ('str',)    2                False            

```


## From/to bytes

```{important}
Depending on your values of `protocol` and `compress` arguments, this feature may require `protobuf` and `lz4` dependencies. You can do `pip install "docarray[full]"` to install it.
```

Serialization into bytes often yield more compact representation than in JSON. Similar to {ref}`the Document serialization<doc-in-bytes>`, DocumentArray can be serialized with different `protocol` and `compress` combinations. In its most simple form,

```python
from docarray import DocumentArray, Document

da = DocumentArray([Document(text='hello'), Document(text='world')])
da.to_bytes()
```

```text
b'\x80\x03cdocarray.array.document\nDocumentArray\nq\x00)\x81q\x01}q\x02(X\x05\x00\x00\x00_dataq\x03]q\x04(cdocarray.document\nDocument\nq\x05) ...
```

```python
da_r = DocumentArray.from_bytes(da.to_bytes())

da_r.summary()
```

```text
                  Documents Summary                   
                                                      
  Length                 2                            
  Homogenous Documents   True                         
  Common Attributes      ('id', 'mime_type', 'text')  
                                                      
                     Attributes Summary                     
                                                            
  Attribute   Data type   #Unique values   Has empty value  
 ────────────────────────────────────────────────────────── 
  id          ('str',)    2                False            
  mime_type   ('str',)    1                False            
  text        ('str',)    2                False      
```

```{tip}
If you go with default `protcol` and `compress` settings, you can simply use `bytes(da)`, which is more Pythonic.
```

The table below summarize the supported serialization protocols and compressions:

| `protocol=...`           | Description                                                                                         | Remarks                                                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| `pickle-array` (default) | Serialize the whole array in one-shot using Python `pickle`                                         | Often fastest. Not portable to other languages. Insecure in production.                                                     |
| `protobuf-array`         | Serialize the whole array using [`DocumentArrayProto`](../../../proto/#docarray.DocumentArrayProto). | Portable to other languages if they implement `DocumentArrayProto`. 2GB max-size (pre-compression) restriction by Protobuf. |
| `pickle`                 | Serialize elements one-by-one using Python `pickle`.                                                | Allow streaming. Not portable to other languages. Insecure in production.                                                   |
| `protobuf`               | Serialize elements one-by-one using [`DocumentProto`](../../../proto/#docarray.DocumentProto). | Allow streaming. Portable to other languages if they implement `DocumentProto`. No max-size restriction                     |

For compressions, the following algorithms are supported: `lz4`, `bz2`, `lzma`, `zlib`, `gzip`. The most frequently used ones are `lz4` (fastest) and `gzip` (most widely used).

If you specified non-default `protocol` and `compress` in {meth}`~docarray.array.mixins.io.binary.BinaryIOMixin.to_bytes`, you will need to specify the same in {meth}`~docarray.array.mixins.io.binary.BinaryIOMixin.from_bytes`.

Depending on the use cases, you can choose the one works best for you. Here is a benchmark on serializing a DocumentArray with one million near-empty Documents (i.e. init with `DocumentArray.empty(...)` where each Document has only `id`).

```{figure} images/benchmark-size.svg
```

```{figure} images/benchmark-time.svg
```

The benchmark was conducted [on the codebase of Jan. 5, 2022](https://github.com/jina-ai/docarray/tree/a56067e486d2318e05bcf6088bd1436040107ad2).  

Depending on how you want to interpret the results, the figures above can be an over-estimation/under-estimation of the serialization latency: one may argue that near-empty Documents are not realistic, but serializing a DocumentArray with one million Documents is also unreal. In practice, DocumentArray passing across microservices are relatively small, say at thousands, for better overlapping the network latency and computational overhead.


### Wire format of `pickle` and `protobuf`

When set `protocol=pickle` or `protobuf`, the result binary string looks like the following:

```text
-----------------------------------------------------------------------------------
| Delimiter |  doc1.to_bytes()  |  Delimiter |  doc2.to_bytes()  | Delimiter | ...
-----------------------------------------------------------------------------------
      |               |
      |               |
      |               |
 Fixed-length         |
                      |
               Variable-length       
```

Here `Delimiter` is a 16-bytes separator such as `b'g\x81\xcc\x1c\x0f\x93L\xed\xa2\xb0s)\x9c\xf9\xf6\xf2'` used for setting the boundary of each Document's serialization. Given a `to_bytes(protocol='pickle/protobuf')` binary string, once we know the first 16 bytes, the boundary is clear. Consequently, one can leverage this format to stream Documents, drop, skip, or early-stop, etc.

## From/to Protobuf

Serializing to Protobuf Message is less frequently used, unless you are using Python Protobuf API. Nonetheless, you can use {meth}`~docarray.array.mixins.io.binary.BinaryIOMixin.from_protobuf` and {meth}`~docarray.array.mixins.io.binary.BinaryIOMixin.to_protobuf` to get a Protobuf Message object in Python.

```python
from docarray import DocumentArray, Document

da = DocumentArray([Document(text='hello'), Document(text='world')])
da.to_bytes()
```

```text
docs {
  id: "2571b8b66e4d11ec9f271e008a366d49"
  text: "hello"
  mime_type: "text/plain"
}
docs {
  id: "2571ba466e4d11ec9f271e008a366d49"
  text: "world"
  mime_type: "text/plain"
}
```

## From/to list

Serializing to/from Python list is less frequently used for the same reason as `Document.to_dict()`: it is often an intermediate step of serializing to JSON. You can do:

```python
from docarray import DocumentArray, Document

da = DocumentArray([Document(text='hello'), Document(text='world')])
da.to_list()
```

```text
[{'id': 'ae55782a6e4d11ec803c1e008a366d49', 'text': 'hello', 'mime_type': 'text/plain'}, {'id': 'ae557a146e4d11ec803c1e008a366d49', 'text': 'world', 'mime_type': 'text/plain'}]
```

There is an argument `strict` shares {ref}`the same semantic<strict-arg-explain>` as in `Document.to_dict()`.

## From/to dataframe

```{important}
This feature requires `pandas` dependency. You can do `pip install "docarray[full]"` to install it.
```

One can convert between a DocumentArray object and a `pandas.dataframe` object.

```python
from docarray import DocumentArray, Document

da = DocumentArray([Document(text='hello'), Document(text='world')])
da.to_dataframe()
```

```text
                                 id   text   mime_type
0  43cb93b26e4e11ec8b731e008a366d49  hello  text/plain
1  43cb95746e4e11ec8b731e008a366d49  world  text/plain
```

To build a DocumentArray from dataframe,

```python
df = ...
da = DocumentArray.from_dataframe(df)
```

## From/to cloud

```{important}
This feature requires `rich` and `requests` dependency. You can do `pip install "docarray[full]"` to install it.
```

{meth}`~docarray.array.mixins.io.pushpull.PushPullMixin.push` and {meth}`~docarray.array.mixins.io.pushpull.PushPullMixin.pull` allows you to serialize a DocumentArray object to Jina Cloud and share it across machines.

Considering you are working on a GPU machine via Google Colab/Jupyter. After preprocessing and embedding, you got everything you need in a DocumentArray. You can easily store it to the cloud via:

```python
from docarray import DocumentArray

da = DocumentArray(...)  # heavylifting, processing, GPU task, ...
da.push(token='myda123')
```

```{figure} images/da-push.png
```

Then on your local laptop, simply pull it:

```python
from docarray import DocumentArray

da = DocumentArray.pull(token='myda123')
```

Now you can continue the work at local, analyzing `da` or visualizing it. Your friends & colleagues who know the token `myda123` can also pull that DocumentArray. It's useful when you want to quickly share the results with your colleagues & friends.

The maximum size of an upload is 4GB under the `protocol='protobuf'` and `compress='gzip'` setting. The lifetime of an upload is one week after its creation.