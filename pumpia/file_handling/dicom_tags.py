"""
Classes and functions relevant to handling dicom tags.

Functions:
 * get_tag

Classes:
 * DicomTags
 * MRTags
 * Tag
 * TagLink
"""
import dataclasses as dc
from dataclasses import dataclass
import pydicom


@dataclass()
class Tag:
    """
    dataclass representing a dicom tag

    Parameters
    ----------
    description : str
        the description/name of the tag as defined in the dicom standards.
    group : int
        the group of the dicom tag
    element : int
        the element of the dicom tag
    links : list[TagLink]
        a list of TagLinks that hold any sequences the tag may be part of.

    Attributes
    ----------
    description : str
    group : int
    element : int
    links : list[TagLink]

    Methods
    -------
    get() -> tuple[int, int]
        return the dicom tag as a tuple
    """
    description: str
    group: int
    element: int
    links: list['TagLink'] = dc.field(default_factory=list)

    def get(self) -> tuple[int, int]:
        """
        returns the tag as a Tuple of (group, element)

        Returns
        -------
        Tuple
            (group, element)
        """
        return (self.group, self.element)

    def __int__(self) -> int:
        return (self.group << 16) | self.element

    def __eq__(self, value) -> bool:
        if isinstance(value, Tag):
            return self.get() == value.get()
        elif isinstance(value, tuple):
            return self.get() == value
        elif isinstance(value, int):
            return int(self) == value
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.get())

    def __str__(self) -> str:
        return f"({self.group:04X}, {self.element:04X})"


@dataclass
class TagLink:
    """
    Class to hold links between tags and sequences

    Parameters
    ----------
    tag : Tag
        the tag of the sequence
    frame_link : bool
        if the link is related to a frame.
        (requires a frame number to access correct value through `get_tag`)
    """
    tag: Tag
    frame_link: bool = False


class DicomTags():
    """
    Class to hold dicom tags.
    DICOM tags are accessed through class attributes
    e.g.`DicomTags.StudyDate` gives the tag representation for study date.
    """
    DimensionIndexSequence = Tag("DimensionIndexSequence",
                                 0x0020,
                                 0x9222)
    SharedFunctionalGroupsSequence = Tag("SharedFunctionalGroupsSequence",
                                         0x5200,
                                         0x9229)
    PerFrameFunctionalGroupsSequence = Tag("PerFrameFunctionalGroupsSequence",
                                           0x5200,
                                           0x9230)

    ReferencedImageSequence = Tag("ReferencedImageSequence",
                                  0x0008,
                                  0x1140,
                                  [TagLink(SharedFunctionalGroupsSequence)])
    FrameAnatomySequence = Tag("FrameAnatomySequence",
                               0x0020,
                               0x9071,
                               [TagLink(SharedFunctionalGroupsSequence)])
    FrameContentSequence = Tag("FrameContentSequence",
                               0x0020,
                               0x9111,
                               [TagLink(PerFrameFunctionalGroupsSequence, True)])
    PlanePositionSequence = Tag("PlanePositionSequence",
                                0x0020,
                                0x9113,
                                [TagLink(PerFrameFunctionalGroupsSequence, True)])
    PlaneOrientationSequence = Tag("PlaneOrientationSequence",
                                   0x0020,
                                   0x9116,
                                   [TagLink(PerFrameFunctionalGroupsSequence, True)])
    PixelMeasuresSequence = Tag("PixelMeasuresSequence",
                                0x0028,
                                0x9110,
                                [TagLink(PerFrameFunctionalGroupsSequence, True)])
    FrameVOILUTSequence = Tag("FrameVOILUTSequence",
                              0x0028,
                              0x9132,
                              [TagLink(PerFrameFunctionalGroupsSequence, True)])
    PixelValueTransformationSequence = Tag("PixelValueTransformationSequence",
                                           0x0028,
                                           0x9145,
                                           [TagLink(PerFrameFunctionalGroupsSequence, True)])
    RealWorldValueMappingSequence = Tag("RealWorldValueMappingSequence",
                                        0x0040,
                                        0x9096,
                                        [TagLink(PerFrameFunctionalGroupsSequence, True)])
    PurposeOfReferenceCodeSequence = Tag("PurposeOfReferenceCodeSequence",
                                         0x0040,
                                         0xA170,
                                         [TagLink(ReferencedImageSequence)])

    ImplementationVersionName = Tag("ImplementationVersionName",
                                    0x0002,
                                    0x0013)

    SpecificCharacterSet = Tag("SpecificCharacterSet",
                               0x0008,
                               0x0005)
    ImageType = Tag("ImageType",
                    0x0008,
                    0x0008)
    StudyDate = Tag("StudyDate",
                    0x0008,
                    0x0020)
    SeriesDate = Tag("SeriesDate",
                     0x0008,
                     0x0021)
    AcquisitionDateTime = Tag("AcquisitionDateTime",
                              0x0008,
                              0x002A)
    StudyTime = Tag("StudyTime",
                    0x0008,
                    0x0030)
    SeriesTime = Tag("SeriesTime",
                     0x0008,
                     0x0031)
    Manufacturer = Tag("Manufacturer",
                       0x0008,
                       0x0070)
    StationName = Tag("StationName",
                      0x0008,
                      0x1010)
    StudyDescription = Tag("StudyDescription",
                           0x0008,
                           0x1030)
    SeriesDescription = Tag("SeriesDescription",
                            0x0008,
                            0x103E)
    ManufacturerModelName = Tag("ManufacturerModelName",
                                0x0008,
                                0x1090)
    ReferencedSOPClassUID = Tag("ReferencedSOPClassUID",
                                0x0008,
                                0x1150,
                                [TagLink(ReferencedImageSequence)])
    ReferencedSOPInstanceUID = Tag("ReferencedSOPInstanceUID",
                                   0x0008,
                                   0x1155,
                                   [TagLink(ReferencedImageSequence)])
    ReferencedFrameNumber = Tag("ReferencedFrameNumber",
                                0x0008,
                                0x1160,
                                [TagLink(ReferencedImageSequence)])
    AnatomicRegionSequence = Tag("AnatomicRegionSequence",
                                 0x0008,
                                 0x2218,
                                 [TagLink(FrameAnatomySequence)])

    PatientName = Tag("PatientName",
                      0x0010,
                      0x0010)
    PatientID = Tag("PatientID",
                    0x0010,
                    0x0020)

    BodyPartExamined = Tag("BodyPartExamined",
                           0x0018,
                           0x0015)
    SliceThickness = Tag("SliceThickness",
                         0x0018,
                         0x0050,
                         [TagLink(PixelMeasuresSequence)])
    SpacingBetweenSlices = Tag("SpacingBetweenSlices",
                               0x0018,
                               0x0088,
                               [TagLink(PixelMeasuresSequence)])
    DeviceSerialNumber = Tag("DeviceSerialNumber",
                             0x0018,
                             0x1000)
    SoftwareVersions = Tag("SoftwareVersions",
                           0x0018,
                           0x1020)
    ProtocolName = Tag("ProtocolName",
                       0x0018,
                       0x1030)

    StudyInstanceUID = Tag("StudyInstanceUID",
                           0x0020,
                           0x000D)
    SeriesInstanceUID = Tag("SeriesInstanceUID",
                            0x0020,
                            0x000E)
    StudyID = Tag("StudyID",
                  0x0020,
                  0x0010)
    SeriesNumber = Tag("SeriesNumber",
                       0x0020,
                       0x0011)
    AcquisitionNumber = Tag("AcquisitionNumber",
                            0x0020,
                            0x0012)
    InstanceNumber = Tag("InstanceNumber",
                         0x0020,
                         0x0013)
    ImagePositionPatient = Tag("ImagePositionPatient",
                               0x0020,
                               0x0032,
                               [TagLink(PlanePositionSequence)])
    ImageOrientationPatient = Tag("ImageOrientationPatient",
                                  0x0020,
                                  0x0037,
                                  [TagLink(PlaneOrientationSequence)])
    SliceLocation = Tag("SliceLocation",
                        0x0020,
                        0x1041)
    StackID = Tag("StackID",
                  0x0020,
                  0x9056,
                  [TagLink(FrameContentSequence)])
    InStackPositionNumber = Tag("InStackPositionNumber",
                                0x0020,
                                0x9057,
                                [TagLink(FrameContentSequence)])
    FrameLaterality = Tag("FrameLaterality",
                          0x0020,
                          0x9072,
                          [TagLink(FrameAnatomySequence)])
    FrameAcquisitionNumber = Tag("FrameAcquisitionNumber",
                                 0x0020,
                                 0x9156,
                                 [TagLink(FrameContentSequence)])
    DimensionIndexValues = Tag("DimensionIndexValues",
                               0x0020,
                               0x9157,
                               [TagLink(FrameContentSequence)])
    DimensionIndexPointer = Tag("DimensionIndexPointer",
                                0x0020,
                                0x9165,
                                [TagLink(DimensionIndexSequence)])
    FunctionalGroupPointer = Tag("FunctionalGroupPointer",
                                 0x0020,
                                 0x9167,
                                 [TagLink(DimensionIndexSequence)])
    DimensionDescriptionLabel = Tag("DimensionDescriptionLabel",
                                    0x0020,
                                    0x9421,
                                    [TagLink(DimensionIndexSequence)])

    SamplesPerPixel = Tag("SamplesPerPixel",
                          0x0028,
                          0x0002)
    PhotometricInterpretation = Tag("PhotometricInterpretation",
                                    0x0028,
                                    0x0004)
    NumberOfFrames = Tag("NumberOfFrames",
                         0x0028,
                         0x0008)
    Rows = Tag("Rows",
               0x0028,
               0x0010)
    Columns = Tag("Columns",
                  0x0028,
                  0x0011)
    PixelSpacing = Tag("PixelSpacing",
                       0x0028,
                       0x0030,
                       [TagLink(PixelMeasuresSequence)])
    BitsAllocated = Tag("BitsAllocated",
                        0x0028,
                        0x0100)
    BitsStored = Tag("BitsStored",
                     0x0028,
                     0x0101)
    HighBit = Tag("HighBit",
                  0x0028,
                  0x0102)
    SmallestImagePixelValue = Tag("SmallestImagePixelValue",
                                  0x0028,
                                  0x0106)
    LargestImagePixelValue = Tag("LargestImagePixelValue",
                                 0x0028,
                                 0x0107)
    WindowCenter = Tag("WindowCenter",
                       0x0028,
                       0x1050,
                       [TagLink(FrameVOILUTSequence)])
    WindowWidth = Tag("WindowWidth",
                      0x0028,
                      0x1051,
                      [TagLink(FrameVOILUTSequence)])
    RescaleIntercept = Tag("RescaleIntercept",
                           0x0028,
                           0x1052,
                           [TagLink(PixelValueTransformationSequence)])
    RescaleSlope = Tag("RescaleSlope",
                       0x0028,
                       0x1053,
                       [TagLink(PixelValueTransformationSequence)])
    RescaleType = Tag("RescaleType",
                      0x0028,
                      0x1054,
                      [TagLink(PixelValueTransformationSequence)])
    LUTExplanation = Tag("LUTExplanation",
                         0x0028,
                         0x3003,
                         [TagLink(RealWorldValueMappingSequence)])
    MeasurementUnitsCodeSequence = Tag("MeasurementUnitsCodeSequence",
                                       0x0040,
                                       0x08EA,
                                       [TagLink(RealWorldValueMappingSequence)])
    LUTLabel = Tag("LUTLabel",
                   0x0040,
                   0x9210,
                   [TagLink(RealWorldValueMappingSequence)])
    RealWorldValueLastValueMapped = Tag("RealWorldValueLastValueMapped",
                                        0x0040,
                                        0x9211,
                                        [TagLink(RealWorldValueMappingSequence)])
    RealWorldValueFirstValueMapped = Tag("RealWorldValueFirstValueMapped",
                                         0x0040,
                                         0x9216,
                                         [TagLink(RealWorldValueMappingSequence)])
    RealWorldValueIntercept = Tag("ealWorldValueIntercept",
                                  0x0040,
                                  0x9224,
                                  [TagLink(RealWorldValueMappingSequence)])
    RealWorldValueSlope = Tag("RealWorldValueSlope",
                              0x0040,
                              0x9225,
                              [TagLink(RealWorldValueMappingSequence)])

    @classmethod
    def list_tags(cls) -> list[Tag]:
        """
        lists all tags

        Returns
        -------
        list[Tag]
            list of tags of type Tag
        """
        attrs = dir(cls)
        tags = []
        for tag in attrs:
            if tag != 'list_tags':
                if isinstance(getattr(cls, tag), Tag):
                    tags.append(getattr(cls, tag))

        return tags

    @classmethod
    def list_tag_tuples(cls) -> list[tuple[int, int]]:
        """
        lists all tags as tuples of (group, element)

        Returns
        -------
        list[tuple[int, int]]
            list of tags
        """
        return [t.get() for t in cls.list_tags()]

    @classmethod
    def tuple_to_tag(cls,
                     tag: tuple[int, int],
                     description: str | None = None,
                     links: list[TagLink] | None = None) -> Tag:
        """
        Converts a tuple to a Tag class.
        If this tag exists in the class attributes
        then the Tag stored in that class attribute is returned.
        Otherwise a new Tag is created.

        Parameters
        ----------
        tag : tuple[int, int]
            the tuple to be converted
        description : str, optional
            the description of the Tag if a new one is created, by default None
        links : list[TagLink], optional
            the links to sequences if a new Tag is created, by default []

        Returns
        -------
        Tag
            object for the tag element provided.

        Raises
        ------
        ValueError
            If the tag can not be found and no description is provided.
        """
        if links is None:
            links = []
        try:
            return cls.list_tags()[cls.list_tag_tuples().index(tag)]
        except ValueError as exc:
            if description is not None:
                return Tag(description, tag[0], tag[1], links)
            else:
                raise ValueError(
                    "tag could not be found and no name was provided") from exc


class MRTags(DicomTags):
    """
    class to hold dicom tags for MRI
    """
    MRImagingModifierSequence = Tag("MRImagingModifierSequence",
                                    0x0018,
                                    0x9006,
                                    [TagLink(DicomTags.SharedFunctionalGroupsSequence)])
    MRReceiveCoilSequence = Tag("MRReceiveCoilSequence",
                                0x0018,
                                0x9042,
                                [TagLink(DicomTags.SharedFunctionalGroupsSequence)])
    MRTransmitCoilSequence = Tag("MRTransmitCoilSequence",
                                 0x0018,
                                 0x9049,
                                 [TagLink(DicomTags.SharedFunctionalGroupsSequence)])

    MRTimingAndRelatedParametersSequence = Tag("MRTimingAndRelatedParametersSequence",
                                               0x0018,
                                               0x9112,
                                               [TagLink(DicomTags.SharedFunctionalGroupsSequence)])
    MRFOVGeometrySequence = Tag("MRFOVGeometrySequence",
                                0x0018,
                                0x9125,
                                [TagLink(DicomTags.SharedFunctionalGroupsSequence)])
    MRModifierSequence = Tag("MRModifierSequence",
                             0x0018,
                             0x9115,
                             [TagLink(DicomTags.SharedFunctionalGroupsSequence)])

    MREchoSequence = Tag("MREchoSequence",
                         0x0018,
                         0x9114,
                         [TagLink(DicomTags.PerFrameFunctionalGroupsSequence, True)])
    MRMetaboliteMapSequence = Tag("MRMetaboliteMapSequence",
                                  0x0018,
                                  0x9152,
                                  [TagLink(DicomTags.PerFrameFunctionalGroupsSequence, True)])
    MRDiffusionSequence = Tag("MRDiffusionSequence",
                              0x0018,
                              0x9117,
                              [TagLink(DicomTags.PerFrameFunctionalGroupsSequence, True)])
    MRAveragesSequence = Tag("MRAveragesSequence",
                             0x0018,
                             0x9119,
                             [TagLink(DicomTags.PerFrameFunctionalGroupsSequence, True),
                              TagLink(DicomTags.SharedFunctionalGroupsSequence)])
    MRImageFrameTypeSequence = Tag("MRImageFrameTypeSequence",
                                   0x0018,
                                   0x9226,
                                   [TagLink(DicomTags.PerFrameFunctionalGroupsSequence, True)])

    MultiCoilDefinitionSequence = Tag("MultiCoilDefinitionSequence",
                                      0x0018,
                                      0x9045,
                                      [TagLink(MRReceiveCoilSequence)])

    FrameType = Tag("FrameType",
                    0x0008,
                    0x9007,
                    [TagLink(MRImageFrameTypeSequence)])
    PixelPresentation = Tag("PixelPresentation",
                            0x0008,
                            0x9205,
                            [TagLink(MRImageFrameTypeSequence)])
    VolumetricProperties = Tag("VolumetricProperties",
                               0x0008,
                               0x9206,
                               [TagLink(MRImageFrameTypeSequence)])
    VolumeBasedCalculationTechnique = Tag("VolumeBasedCalculationTechnique",
                                          0x0008,
                                          0x9207,
                                          [TagLink(MRImageFrameTypeSequence)])
    ComplexImageComponent = Tag("ComplexImageComponent",
                                0x0008,
                                0x9208,
                                [TagLink(MRImageFrameTypeSequence)])
    AcquisitionContrast = Tag("AcquisitionContrast",
                              0x0008,
                              0x9209,
                              [TagLink(MRImageFrameTypeSequence)])

    MRAcquisitionType = Tag("MRAcquisitionType",
                            0x0018,
                            0x0023)

    RepetitionTime = Tag("RepetitionTime",
                         0x0018,
                         0x0080,
                         [TagLink(MRTimingAndRelatedParametersSequence)])
    EchoTime = Tag("EchoTime",
                   0x0018,
                   0x0081)
    InversionTime = Tag("InversionTime",
                        0x0018,
                        0x0082,
                        [TagLink(MRTimingAndRelatedParametersSequence)])
    NumberOfAverages = Tag("NumberOfAverages",
                           0x0018,
                           0x0083,
                           [TagLink(MRAveragesSequence)])
    ImagingFrequency = Tag("ImagingFrequency",
                           0x0018,
                           0x0084)
    ImagedNucleus = Tag("ImagedNucleus",
                        0x0018,
                        0x0085)
    EchoNumbers = Tag("EchoNumbers",
                      0x0018,
                      0x0086,
                      [TagLink(MREchoSequence)])
    MagneticFieldStrength = Tag("MagneticFieldStrength",
                                0x0018,
                                0x0087)
    NumberOfPhaseEncodingSteps = Tag("NumberOfPhaseEncodingSteps",
                                     0x0018,
                                     0x0089)
    EchoTrainLength = Tag("EchoTrainLength",
                          0x0018,
                          0x0091,
                          [TagLink(MRTimingAndRelatedParametersSequence)])
    PercentSampling = Tag("PercentSampling",
                          0x0018,
                          0x0093,
                          [TagLink(MRFOVGeometrySequence)])
    PercentPhaseFieldOfView = Tag("PercentPhaseFieldOfView",
                                  0x0018,
                                  0x0094,
                                  [TagLink(MRFOVGeometrySequence)])
    PixelBandwidth = Tag("PixelBandwidth",
                         0x0018,
                         0x0095,
                         [TagLink(MRImagingModifierSequence)])

    ReceiveCoilName = Tag("ReceiveCoilName",
                          0x0018,
                          0x1250,
                          [TagLink(MRReceiveCoilSequence)])
    TransmitCoilName = Tag("TransmitCoilName",
                           0x0018,
                           0x1251,
                           [TagLink(MRTransmitCoilSequence)])
    InPlanePhaseEncodingDirection = Tag("InPlanePhaseEncodingDirection",
                                        0x0018,
                                        0x1312,
                                        [TagLink(MRFOVGeometrySequence)])
    FlipAngle = Tag("FlipAngle",
                    0x0018,
                    0x1314,
                    [TagLink(MRTimingAndRelatedParametersSequence)])
    SAR = Tag("SAR",
              0x0018,
              0x1316)
    dBdt = Tag("dBdt",
               0x0018,
               0x1318)
    B1rms = Tag("B1rms",
                0x0018,
                0x1320)
    PatientPosition = Tag("PatientPosition",
                          0x0018,
                          0x5100)
    PulseSequenceName = Tag("PulseSequenceName",
                            0x0018,
                            0x9005)
    EchoPulseSequence = Tag("EchoPulseSequence",
                            0x0018,
                            0x9008)
    InversionRecovery = Tag("InversionRecovery",
                            0x0018,
                            0x9009,
                            [TagLink(MRModifierSequence)])
    FlowCompensation = Tag("FlowCompensation",
                           0x0018,
                           0x9010,
                           [TagLink(MRModifierSequence)])
    MultipleSpinEcho = Tag("MultipleSpinEcho",
                           0x0018,
                           0x9011)
    MultiPlanarExcitation = Tag("MultiPlanarExcitation",
                                0x0018,
                                0x9012)
    PhaseContrast = Tag("PhaseContrast",
                        0x0018,
                        0x9014)
    TimeOfFlightContrast = Tag("TimeOfFlightContrast",
                               0x0018,
                               0x9015)
    SteadyStatePulseSequence = Tag("SteadyStatePulseSequence",
                                   0x0018,
                                   0x9017)
    EchoPlanarPulseSequence = Tag("EchoPlanarPulseSequence",
                                  0x0018,
                                  0x9018)
    MagnetizationTransfer = Tag("MagnetizationTransfer",
                                0x0018,
                                0x9020,
                                [TagLink(MRImagingModifierSequence)])
    T2Preparation = Tag("T2Preparation",
                        0x0018,
                        0x9021,
                        [TagLink(MRModifierSequence)])
    BloodSignalNulling = Tag("BloodSignalNulling",
                             0x0018,
                             0x9022,
                             [TagLink(MRImagingModifierSequence)])
    SaturationRecovery = Tag("SaturationRecovery",
                             0x0018,
                             0x9024)
    SpectrallySelectedSuppression = Tag("SpectrallySelectedSuppression",
                                        0x0018,
                                        0x9025)
    SpectrallySelectedExcitation = Tag("SpectrallySelectedExcitation",
                                       0x0018,
                                       0x9026,
                                       [TagLink(MRModifierSequence)])
    SpatialPresaturation = Tag("SpatialPresaturation",
                               0x0018,
                               0x9027,
                               [TagLink(MRModifierSequence)])
    Tagging = Tag("Tagging",
                  0x0018,
                  0x9028,
                  [TagLink(MRImagingModifierSequence)])
    OversamplingPhase = Tag("OversamplingPhase",
                            0x0018,
                            0x9029)
    GeometryOfKSpaceTraversal = Tag("GeometryOfKSpaceTraversal",
                                    0x0018,
                                    0x9032)
    SegmentedKSpaceTraversal = Tag("SegmentedKSpaceTraversal",
                                   0x0018,
                                   0x9033)
    RectilinearPhaseEncodeReordering = Tag("RectilinearPhaseEncodeReordering",
                                           0x0018,
                                           0x9034)
    PartialFourierDirection = Tag("PartialFourierDirection",
                                  0x0018,
                                  0x9036,
                                  [TagLink(MRModifierSequence)])
    ReceiveCoilManufacturerName = Tag("ReceiveCoilManufacturerName",
                                      0x0018,
                                      0x9041,
                                      [TagLink(MRReceiveCoilSequence)])
    ReceiveCoilType = Tag("ReceiveCoilType",
                          0x0018,
                          0x9043,
                          [TagLink(MRReceiveCoilSequence)])
    QuadratureReceiveCoil = Tag("QuadratureReceiveCoil",
                                0x0018,
                                0x9044,
                                [TagLink(MRReceiveCoilSequence)])
    MultiCoilElementName = Tag("MultiCoilElementName",
                               0x0018,
                               0x9047,
                               [TagLink(MultiCoilDefinitionSequence)])
    MultiCoilElementUsed = Tag("MultiCoilElementUsed",
                               0x0018,
                               0x9048,
                               [TagLink(MultiCoilDefinitionSequence)])
    TransmitCoilManufacturerName = Tag("TransmitCoilManufacturerName",
                                       0x0018,
                                       0x9050,
                                       [TagLink(MRTransmitCoilSequence)])
    TransmitCoilType = Tag("TransmitCoilType",
                           0x0018,
                           0x9051,
                           [TagLink(MRTransmitCoilSequence)])
    MRAcquisitionFrequencyEncodingSteps = Tag("MRAcquisitionFrequencyEncodingSteps",
                                              0x0018,
                                              0x9058,
                                              [TagLink(MRFOVGeometrySequence)])
    KSpaceFiltering = Tag("KSpaceFiltering",
                          0x0018,
                          0x9064)
    ParallelReductionFactorInPlane = Tag("ParallelReductionFactorInPlane",
                                         0x0018,
                                         0x9069,
                                         [TagLink(MRModifierSequence)])
    AcquisitionDuration = Tag("AcquisitionDuration",
                              0x0018,
                              0x9073)
    DiffusionDirectionality = Tag("DiffusionDirectionality",
                                  0x0018,
                                  0x9075,
                                  [TagLink(MRDiffusionSequence)])
    ParallelAcquisition = Tag("ParallelAcquisition",
                              0x0018,
                              0x9077,
                              [TagLink(MRModifierSequence)])
    ParallelAcquisitionTechnique = Tag("ParallelAcquisitionTechnique",
                                       0x0018,
                                       0x9078,
                                       [TagLink(MRModifierSequence)])
    MetaboliteMapDescription = Tag("MetaboliteMapDescription",
                                   0x0018,
                                   0x9080,
                                   [TagLink(MRMetaboliteMapSequence)])
    PartialFourier = Tag("PartialFourier",
                         0x0018,
                         0x9081,
                         [TagLink(MRModifierSequence)])
    EffectiveEchoTime = Tag("EffectiveEchoTime",
                            0x0018,
                            0x9082,
                            [TagLink(MREchoSequence)])
    DiffusionBValue = Tag("DiffusionBValue",
                          0x0018,
                          0x9087,
                          [TagLink(MRDiffusionSequence)])
    DiffusionGradientOrientation = Tag("DiffusionGradientOrientation",
                                       0x0018,
                                       0x9089)
    NumberOfKSpaceTrajectories = Tag("NumberOfKSpaceTrajectories",
                                     0x0018,
                                     0x9093)
    TransmitterFrequency = Tag("TransmitterFrequency",
                               0x0018,
                               0x9098,
                               [TagLink(MRImagingModifierSequence)])
    ResonantNucleus = Tag("ResonantNucleus",
                          0x0018,
                          0x9100)
    ParallelReductionFactorOutOfPlane = Tag("ParallelReductionFactorOutOfPlane",
                                            0x0018,
                                            0x9155,
                                            [TagLink(MRModifierSequence)])
    MRAcquisitionPhaseEncodingStepsInPlane = Tag("MRAcquisitionPhaseEncodingStepsInPlane",
                                                 0x0018,
                                                 0x9231,
                                                 [TagLink(MRFOVGeometrySequence)])
    MRAcquisitionPhaseEncodingStepsOutOfPlane = Tag("MRAcquisitionPhaseEncodingStepsOutOfPlane",
                                                    0x0018,
                                                    0x9232,
                                                    [TagLink(MRFOVGeometrySequence)])
    RFEchoTrainLength = Tag("RFEchoTrainLength",
                            0x0018,
                            0x9240,
                            [TagLink(MRTimingAndRelatedParametersSequence)])
    GradientEchoTrainLength = Tag("GradientEchoTrainLength",
                                  0x0018,
                                  0x9241,
                                  [TagLink(MRTimingAndRelatedParametersSequence)])


def get_tag(dicom_image: pydicom.Dataset | pydicom.DataElement,
            tag: Tag,
            frame: int | None = None) -> pydicom.DataElement:
    """
    Returns the dicom element from the pydicom Dataset defined by tag.
    If the Dataset is a stack then the frame can be provided for frame specific elements.

    Parameters
    ----------
    dicom_image : Dataset
        pydicom Dataset to be searched
    tag : Tag
        tag of element to be returned
    frame : int, optional
        frame number (starting at 1) if relevant, by default None

    Returns
    -------
    DataElement
        pydicom Dataelement of the provided tag.
        Use DataElement.value attribute to get the value of the element.

    Raises
    ------
    KeyError
        raised if an element is not found.
    """
    element = None

    try:
        element = dicom_image[int(tag)]
    except KeyError:
        pass

    sequence = None
    for seq in tag.links:
        try:
            if seq.frame_link and frame is not None:
                sequence = get_tag(dicom_image, seq.tag, frame).value
                element = sequence[frame - 1][tag.get()]
            elif not seq.frame_link:
                sequence = get_tag(dicom_image, seq.tag, frame).value
                element = sequence[0][tag.get()]
        except KeyError:
            pass

    if element is None:
        raise KeyError(tag.get())

    return element
