import unittest
from automations.linguistic_bits import LinguisticTag, ParadigmaFormId

class TestLinguisticTag(unittest.TestCase):
    def test_linguistic_tag_creation(self):
        tag = LinguisticTag("NCIIBN1", "DS")
        self.assertEqual(tag.paradigm_tag, "NCIIBN1")
        self.assertEqual(tag.form_tag, "DS")
        
    def test_linguistic_tag_string_representation(self):
        tag = LinguisticTag("NCIIBN1", "DS")
        self.assertEqual(str(tag), "NCIIBN1|DS")

    def test_partial_linguistic_tag_string_representation_1(self):
        tag = LinguisticTag("NCIIBN1", None)
        self.assertEqual(str(tag), "NCIIBN1|")

    def test_partial_linguistic_tag_string_representation_2(self):
        tag = LinguisticTag(None, '.S')
        self.assertEqual(str(tag), "|.S")
        
    def test_parse_full(self):
        tag = LinguisticTag.from_string("NCIIBN1|DS")
        self.assertIsNotNone(tag)
        self.assertEqual(tag.paradigm_tag, "NCIIBN1")
        self.assertEqual(tag.form_tag, "DS")
    
    def test_parse_partial(self):
        tag = LinguisticTag.from_string("NC.....|")
        self.assertIsNotNone(tag)
        self.assertEqual(tag.paradigm_tag, "NC.....")
        self.assertIsNone(tag.form_tag)

    def test_parse_partial_incomplete(self):
        tag = LinguisticTag.from_string("NC.....")
        self.assertIsNotNone(tag)
        self.assertEqual(tag.paradigm_tag, "NC.....")
        self.assertIsNone(tag.form_tag, None)

    def text_parse_form_without_paradigm(self):
        tag = (LinguisticTag.from_string("|DS"))
        self.assertIsNotNone(tag)
        self.assertIsNone(tag.paradigm_tag)
        self.assertEqual(tag.form_tag, "DS")
        
    def text_non_parseable(self):
        self.assertIsNone(LinguisticTag.from_string(""))
        self.assertIsNone(LinguisticTag.from_string("NC,,,,"))

class TestParadigmaFormId(unittest.TestCase):
    def test_paradigma_form_id_creation(self):
        form_id = ParadigmaFormId(1250379, "a", "DS")
        self.assertEqual(form_id.paradigm_id, 1250379)
        self.assertEqual(form_id.variant_id, "a")
        self.assertEqual(form_id.form_tag, "DS")
        
    def test_paradigma_form_id_string_representation(self):
        form_id = ParadigmaFormId(1250379, "a", "DS")
        self.assertEqual(str(form_id), "1250379a.DS")

    def test_partial_representation_1(self):
        form_id = ParadigmaFormId(1250379, "b", None)
        self.assertEqual(str(form_id), "1250379b.")

    def test_partial_representation_2(self):
        form_id = ParadigmaFormId(1250379, None, None)
        self.assertEqual(str(form_id), "1250379.")

    def test_paradigma_form_id_parsing_full(self):
        form_id = ParadigmaFormId.from_string("1250379a.DS")
        self.assertIsNotNone(form_id)
        self.assertEqual(form_id.paradigm_id, 1250379)
        self.assertEqual(form_id.variant_id, "a")
        self.assertEqual(form_id.form_tag, "DS")
        
    def test_paradigma_form_id_parsing_partial_1(self):
        form_id = ParadigmaFormId.from_string("1250379a")
        self.assertIsNotNone(form_id)
        self.assertEqual(form_id.paradigm_id, 1250379)
        self.assertEqual(form_id.variant_id, "a")
        self.assertIsNone(form_id.form_tag)
        
    def test_paradigma_form_id_parsing_partial_2(self):
        form_id = ParadigmaFormId.from_string("1250379")
        self.assertIsNotNone(form_id)
        self.assertEqual(form_id.paradigm_id, 1250379)
        self.assertIsNone(form_id.variant_id)
        self.assertIsNone(form_id.form_tag)
        
    def test_paradigma_form_id_parsing_permissive_form_absense(self):
        form_id = ParadigmaFormId.from_string("1250379.DP")
        self.assertIsNotNone(form_id)
        self.assertEqual(form_id.paradigm_id, 1250379)
        self.assertIsNone(form_id.variant_id)
        self.assertEqual(form_id.form_tag, "DP")
        
    def test_non_parseable(self):
        self.assertIsNone(ParadigmaFormId.from_string(""))
        self.assertIsNone(ParadigmaFormId.from_string("a.DS"))

class TestParadigmaFormIdIntersection(unittest.TestCase):
    def test_full_intersection(self):
        id1 = ParadigmaFormId(123, "a", "DS")
        id2 = ParadigmaFormId(123, "a", "DS")
        result = id1.intersect_with(id2)
        self.assertEqual(result.paradigm_id, 123)
        self.assertEqual(result.variant_id, "a")
        self.assertEqual(result.form_tag, "DS")

    def test_partial_intersection(self):
        id1 = ParadigmaFormId(123, "a", "DS")
        id2 = ParadigmaFormId(123, "b", "DS")
        result = id1.intersect_with(id2)
        self.assertEqual(result.paradigm_id, 123)
        self.assertIsNone(result.variant_id)
        self.assertEqual(result.form_tag, "DS")

    def test_no_intersection(self):
        id1 = ParadigmaFormId(123, "a", "DS")
        id2 = ParadigmaFormId(124, "a", "DS")
        result = id1.intersect_with(id2)
        self.assertIsNone(result)

    def test_intersection_with_none(self):
        id1 = ParadigmaFormId(123, "a", "DS")
        result = id1.intersect_with(None)
        self.assertIsNone(result)

class TestParadigmaFormIdUnion(unittest.TestCase):
    def test_full_union(self):
        id1 = ParadigmaFormId(123, "a", "DS")
        id2 = ParadigmaFormId(123, "a", "DS")
        result = id1.union_with(id2)
        self.assertEqual(result.paradigm_id, 123)
        self.assertEqual(result.variant_id, "a")
        self.assertEqual(result.form_tag, "DS")

    def test_partial_union(self):
        id1 = ParadigmaFormId(123, None, "DS")
        id2 = ParadigmaFormId(123, "a", None)
        result = id1.union_with(id2)
        self.assertEqual(result.paradigm_id, 123)
        self.assertEqual(result.variant_id, "a")
        self.assertEqual(result.form_tag, "DS")

    def test_union_with_none(self):
        id1 = ParadigmaFormId(123, "a", "DS")
        result = id1.union_with(None)
        self.assertEqual(result.paradigm_id, 123)
        self.assertEqual(result.variant_id, "a")
        self.assertEqual(result.form_tag, "DS")

class TestLinguisticTagIntersection(unittest.TestCase):
    def test_full_intersection(self):
        tag1 = LinguisticTag("NCIIBN1", "DS")
        tag2 = LinguisticTag("NCIIBN1", "DS")
        result = tag1.intersect_with(tag2)
        self.assertEqual(result.paradigm_tag, "NCIIBN1")
        self.assertEqual(result.form_tag, "DS")

    def test_partial_intersection(self):
        tag1 = LinguisticTag("NCI.BN1", "DS")
        tag2 = LinguisticTag("NCIIBN2", "DP")
        result = tag1.intersect_with(tag2)
        self.assertEqual(result.paradigm_tag, "NCI.BN.")
        self.assertEqual(result.form_tag, "D.")

    def test_no_intersection_different_pos(self):
        tag1 = LinguisticTag("NCIIBN1", "DS")
        tag2 = LinguisticTag("VCIBN1", "DS")
        result = tag1.intersect_with(tag2)
        self.assertIsNone(result)

    def test_intersection_with_none(self):
        tag1 = LinguisticTag("NCIIBN1", "DS")
        result = tag1.intersect_with(None)
        self.assertIsNone(result)

class TestLinguisticTagUnion(unittest.TestCase):
    def test_full_union(self):
        tag1 = LinguisticTag("NCIIBN1", "DS")
        tag2 = LinguisticTag("NCIIBN1", "DS")
        result = tag1.union_with(tag2)
        self.assertEqual(result.paradigm_tag, "NCIIBN1")
        self.assertEqual(result.form_tag, "DS")

    def test_partial_union(self):
        tag1 = LinguisticTag("NCIIBN1", None)
        tag2 = LinguisticTag("NCIIBN1", "DS")
        result = tag1.union_with(tag2)
        self.assertEqual(result.paradigm_tag, "NCIIBN1")
        self.assertEqual(result.form_tag, "DS")

    def test_union_with_none(self):
        tag1 = LinguisticTag("NCIIBN1", "DS")
        result = tag1.union_with(None)
        self.assertEqual(result.paradigm_tag, "NCIIBN1")
        self.assertEqual(result.form_tag, "DS")

if __name__ == '__main__':
    unittest.main() 