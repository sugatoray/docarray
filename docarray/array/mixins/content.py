from typing import List, Sequence, TYPE_CHECKING, Optional, Union

from ...math.ndarray import ravel, unravel

if TYPE_CHECKING:
    from ...types import ArrayType, DocumentContentType


class ContentPropertyMixin:
    """Helpers that provide faster getter & setter for :attr:`.content` by using protobuf directly. """

    def _check_length(self, target_len: int):
        if target_len != len(self):
            raise ValueError(
                f'Length must match {self!r}, but {target_len} != {len(self)}'
            )

    @property
    def embeddings(self) -> Optional['ArrayType']:
        """Return a :class:`ArrayType` stacking all the `embedding` attributes as rows.

        :return: a :class:`ArrayType` of embedding
        """
        if self:
            return unravel(self, 'embedding')

    @embeddings.setter
    def embeddings(self, value: 'ArrayType'):
        """Set the :attr:`.embedding` of the Documents.

        To remove all embeddings of all Documents:
        .. highlight:: python
        .. code-block:: python

            da.embeddings = None

        :param value: The embedding matrix to set
        """

        if value is None:
            for d in self:
                d.embedding = None
        else:
            emb_shape0 = _get_len(value)
            self._check_length(emb_shape0)
            ravel(value, self, 'embedding')

    @property
    def blobs(self) -> Optional['ArrayType']:
        """Return a :class:`ArrayType` stacking all :attr:`.blob`.

        The `blob` attributes are stacked together along a newly created first
        dimension (as if you would stack using ``np.stack(X, axis=0)``).

        .. warning:: This operation assumes all blobs have the same shape and dtype.
                 All dtype and shape values are assumed to be equal to the values of the
                 first element in the DocumentArray

        :return: a :class:`ArrayType` of blobs
        """
        if self and self[0].content_type == 'blob':
            if self:
                return unravel(self, 'blob')

    @blobs.setter
    def blobs(self, value: 'ArrayType'):
        """Set :attr:`.blob` of the Documents. To clear all :attr:`blob`, set it to ``None``.

        :param value: The blob array to set. The first axis is the "row" axis.
        """

        if value is None:
            for d in self:
                d.blob = None
        else:
            blobs_shape0 = _get_len(value)
            self._check_length(blobs_shape0)

            ravel(value, self, 'blob')

    @property
    def texts(self) -> Optional[List[str]]:
        """Get :attr:`.text` of all Documents

        :return: a list of texts
        """
        if self and self[0].content_type == 'text':
            if self:
                return [d.text for d in self]

    @texts.setter
    def texts(self, value: Sequence[str]):
        """Set :attr:`.text` for all Documents. To clear all :attr:`text`, set it to ``None``.

        :param value: A sequence of texts to set, should be the same length as the
            number of Documents
        """
        if value is None:
            for d in self:
                d.text = None
        else:
            self._check_length(len(value))

            for doc, text in zip(self, value):
                doc.text = text

    @property
    def buffers(self) -> Optional[List[bytes]]:
        """Get the buffer attribute of all Documents.

        :return: a list of buffers
        """
        if self and self[0].content_type == 'buffer':
            if self:
                return [d.buffer for d in self]

    @buffers.setter
    def buffers(self, value: List[bytes]):
        """Set the buffer attribute for all Documents. To clear all :attr:`buffer`, set it to ``None``.

        :param value: A sequence of buffer to set, should be the same length as the
            number of Documents
        """

        if value is None:
            for d in self:
                d.buffer = None
        else:
            self._check_length(len(value))

            for doc, buffer in zip(self, value):
                doc.buffer = buffer

    @property
    def contents(self) -> Optional[Union[Sequence['DocumentContentType'], 'ArrayType']]:
        """Get the :attr:`.content` of all Documents.

        :return: a list of texts, buffers or :class:`ArrayType`
        """
        if self:
            content_type = self[0].content_type
            if content_type:
                return getattr(self, f'{self[0].content_type}s')

    @contents.setter
    def contents(
        self, value: Sequence[Union[Sequence['DocumentContentType'], 'ArrayType']]
    ):
        """Set the :attr:`.content` of all Documents.

        :param value: a list of texts, buffers or :class:`ArrayType`
        """
        if self:
            content_type = self[0].content_type
            if content_type:
                setattr(self, f'{self[0].content_type}s', value)


def _get_len(value):
    return len(value) if isinstance(value, (list, tuple)) else value.shape[0]
