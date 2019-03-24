# coding=utf-8
""" The kaf version of the graph builder

"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import sys

from corefgraph.graph.syntactic import SyntacticTreeUtils

__author__ = 'Josu Bermudez <josu.bermudez@deusto.es>'


from ..graph.builder import BaseGraphBuilder
from ..graph.wrapper import GraphWrapper
from ..graph.syntactic import POS
from ..resources import tree
from ..resources.tagset import ner_tags, constituent_tags


from collections import defaultdict, deque
from operator import itemgetter
import logging
#TODO Change how reader is manage!
READER = None


class KafAndTreeGraphBuilder(BaseGraphBuilder):
    """Extract the info from KAF documents and TreeBank."""
    kaf_document_property = "kaf"
    kaf_id_property = "kaf_id"
    kaf_offset_property = "offset"

    def __init__(self, reader_name, secure_tree=True, logger=logging.getLogger("GraphBuilder")):
        super(KafAndTreeGraphBuilder, self).__init__()
        global READER
        if reader_name == "NAF":
            import pynaf
            reader = pynaf
            if sys.version_info.major >= 3:
                READER = reader.NAFDocument
            else:
                READER = reader
            self.document_reader = reader.NAFDocument
        elif reader_name == "KAF":
            import pykaf
            reader = pykaf
            if sys.version_info.major >= 3:
                READER = reader.KafDocument
            else:
                READER = reader
            self.document_reader = reader.KafDocument
        else:
            raise Exception("Unknown Reader")
        self.secure_tree = secure_tree
        self.logger = logger
        self.syntax_count = 0
        self.leaf_count = 0
        self.kaf = None
        self.sentence_order = 0
        self.utterance = -1
        self.speakers = []
        self.max_utterance = 1
        self.terms_pool = []
        self.term_by_id = dict()
        self.term_by_word_id = dict()
        self.entities_by_word = defaultdict(set)
        self._sentences = None
        self.graph_utils = None

    def set_graph(self, graph):
        """ Set the graph where this builders works
        @param graph: The graph target of this builder
        """
        super(self.__class__, self).set_graph(graph)
        self.graph_utils = SyntacticTreeUtils(graph)

    def get_graph_utils(self):
        """  Returns a object that provide complex relation finder for graph nodes.
        @return: The utility object
        """
        return self.graph_utils

    def process_document(self, graph, document):
        """ Get a document and prepare the graph an the graph builder to sentence by sentence
         processing of the document.
        @param graph: The graph where the kaf info is loaded
        @param document: A tuple that contains (the KAF,Sentences or none, speakers or none)
        """
        self.graph = graph
        # Counter to order the sentences inside a text. A easier way to work with sentences that order
        self.sentence_order = 1
        if document[1]:
            self._sentences = document[1].strip().split("\n")
        # If speaker is None store None otherwise store split speaker file
        if document[2]:
            # Remove the blank lines and split
            self.speakers = []
            current_speaker = None
            self.max_utterance = -1
            for line in document[2].split("\n"):
                if line == "":
                    continue
                self.speakers.append(line)
                if current_speaker != line:
                    self.max_utterance += 1
                    current_speaker = line

            # A doc is a conversation if exist two o more speakers in it
        else:
            self.speakers = []
            self.max_utterance = 1
        self.utterance = 0
        self._parse_kaf(kaf_string=document[0].strip())

    def get_sentences(self):
        """ Get the sentences of the document.

        @return: A list of trees(kaf nodes or PennTreebank strings)
        """
        if self._sentences:
            return self._sentences
        else:
            return self.kaf.get_constituency_trees()

    def _parse_kaf(self, kaf_string):
        """ Parse all the kaf info tho the graph except of sentence parsing.

        @param kaf_string:
        """
        self.terms_pool = []
        # Store original kaf for further recreation
        self.kaf = self.document_reader(input_stream=kaf_string)
        GraphWrapper.set_graph_property(self.graph, self.kaf_document_property, self.kaf)
        self._set_terms(self.kaf)
        self._set_entities(self.kaf)
        self._set_mentions(self.kaf)
        self._set_dependencies(self.kaf)

    def _set_terms(self, kaf):
        """ Extract the terms of the kaf and add to the graph

        @param kaf: The kaf file manager
        """
        # Words
        kaf_words = dict([
            (kaf_word.attrib[READER.WORD_ID_ATTRIBUTE], kaf_word) for kaf_word in kaf.get_words()])
        # Terms
        self.term_by_id = dict()
        self.term_by_word_id = dict()
        prev_speaker = None
        if self.max_utterance > 1:
            doc_type_value = self.doc_conversation
        else:
            doc_type_value = self.doc_article
        inside_utterance = deque()
        inside_plain_quotes = False
        for term in kaf.get_terms():
            term_id = term.attrib[READER.TERM_ID_ATTRIBUTE]
            # Fetch the words of the term values
            term_words = sorted((kaf_words[word.attrib["id"]] for word in kaf.get_terms_words(term)),
                                key=lambda x: x.attrib[self.kaf_offset_property])
            # Build term attributes
            form = self._expand_kaf_word(term_words)
            order = int(term_words[0].attrib[READER.WORD_ID_ATTRIBUTE][1:]), \
                int(term_words[-1].attrib[READER.WORD_ID_ATTRIBUTE][1:])
            span = order
            begin = int(term_words[0].attrib[self.kaf_offset_property])
            end = int(term_words[-1].attrib[self.kaf_offset_property]) + int(term_words[-1].attrib["length"]) - 1
            # We want pennTreeBank tagging no kaf tagging
            pos = term.attrib[READER.MORPHOFEAT_ATTRIBUTE]
            kaf_id = "{0}#{1}".format(term_id, "|".join([word.attrib[READER.WORD_ID_ATTRIBUTE] for word in term_words]))
            # Clear unicode problems
#            if isinstance(form, unicode):
            form = form.encode("utf8")
            try:
                lemma = term.attrib[READER.LEMMA_ATTRIBUTE]
                if lemma == "-":
                    raise KeyError
            except KeyError:
                lemma = form
#            if isinstance(lemma, unicode):
            lemma = lemma #.encode("utf8")

            label = "\n".join((str(form), str(pos), str(lemma), str(term_id)))
            #Create word node
            word_node = self.add_word(
                form=form, node_id=term_id, label=label, lemma=lemma, pos=pos, order=order,
                begin=begin, end=end)
            word_node["span"] = span
            word_node[self.kaf_id_property] = kaf_id
            word_node["prev_speaker"] = prev_speaker
            if self.speakers:
                speaker = self.speakers.pop(0).replace("_", " ")
                if not speaker or speaker == "-":
                    form_speaker = "PER{0}".format(self.utterance)
                else:
                    form_speaker = speaker
                if prev_speaker != speaker:
                    if prev_speaker is not None:
                        self.utterance += 1
                    prev_speaker = speaker
            else:
                form_speaker = "PER{0}".format(self.utterance)

            # Manage Quotation
            # TODO improve  nested quotation
            if form == "``" or (form == '"' and not inside_plain_quotes):
                self.max_utterance += 1
                inside_utterance.append(self.max_utterance)
                if form == '"':
                    inside_plain_quotes = True
            elif form == "''" or (form == '"' and inside_plain_quotes):
                if form == '"':
                    inside_plain_quotes = False
                try:
                    inside_utterance.pop()
                except IndexError:
                    self.logger.warning("Unbalanced quotes")

            if len(inside_utterance):
                word_node["utterance"] = inside_utterance[-1]
                word_node["speaker"] = "PER{0}".format(inside_utterance[-1])
                word_node["quoted"] = True
            else:
                word_node["speaker"] = form_speaker
                word_node["utterance"] = self.utterance
                word_node["quoted"] = False

            word_node[self.doc_type] = doc_type_value
            # Store term
            # ONLY FOR STANFORD DEPENDENCIES IN KAF
            for word in term_words:
                self.term_by_word_id[word.attrib[READER.WORD_ID_ATTRIBUTE]] = word_node
            self.term_by_id[term_id] = word_node
            self.terms_pool.append(word_node)
            self.statistics_word_up()
        self.leaf_count = 0

    def _set_entities(self, kaf):
        """ Extract the entities of the kaf and add to the file

        @param kaf: The kaf file manager
        """
        # A dict of entities that contains a list of references. A reference is a list of terms.
        self.entities_by_word = defaultdict(list)
        for kaf_entity in kaf.get_entities():
            entity_type = kaf_entity.attrib["type"]
            entity_id = kaf_entity.attrib[READER.NAMED_ENTITY_ID_ATTRIBUTE]
            for reference in kaf.get_entity_references(kaf_entity):
                # Fetch terms
                entity_terms = sorted(
                    [self.term_by_id[term.attrib["id"]] for term in kaf.get_reference_span(reference)],
                    key=itemgetter("ord"))
                # attach 's if exist
                next_term = self.term_by_id.get("t{0}".format(int(entity_terms[-1]["id"][1:]) + 1))
                if next_term and next_term["form"] == "'s":
                    entity_terms.append(next_term)
                    # Convert ID into terms
                # Build form
                form = self._expand_node(entity_terms)
                # Build the entity
                label = "{0} | {1}".format(form, entity_type)
                entity = self.add_named_entity(entity_type=entity_type, entity_id=entity_id, label=label)
                # Set the other attributes
                entity["begin"] = entity_terms[0]["begin"]
                entity["end"] = entity_terms[-1]["end"]
                entity["form"] = form
                entity["ord"] = entity_terms[0]["span"][0], entity_terms[-1]["span"][1]
                entity["span"] = entity["ord"]

                # Link words_ids to mention as word
                for term in entity_terms:
                    self.link_word(entity, term)
                # Index the entity by its first word
                first_word_id = entity_terms[0]["id"]
                self.entities_by_word[first_word_id].append(entity)

    def _set_mentions(self, kaf):
        """ Extract the entities of the kaf and add to the file

        @param kaf: The kaf file manager
        """
        # A dict of entities that contains a list of references. A reference is a list of terms.
        self.mentions_by_word = defaultdict(list)
        for kaf_entity in kaf.get_coreference():
            entity_id = kaf_entity.attrib[READER.COREFERENCE_ID_ATTRIBUTE]
            counter = 0
            for reference in kaf.get_coreference_mentions(kaf_entity):
                counter += 1
                # Fetch terms
                entity_terms = sorted(
                    [self.term_by_id[term.attrib["id"]] for term in set(kaf.get_reference_span(reference))],
                    key=itemgetter("ord"))
                # Build form
                form = self._expand_node(entity_terms)
                # Build the entity
                label = "{0} | {1}".format(form, "Gold")
                entity = self.add_gold_mention(gold_mention_id="{0}#{1}".format(entity_id, counter), label=label)
                # Set the other attributes
                entity["begin"] = entity_terms[0]["begin"]
                entity["end"] = entity_terms[-1]["end"]
                entity["form"] = form
                entity["ord"] = entity_terms[0]["span"][0], entity_terms[-1]["span"][1]
                entity["span"] = entity["ord"]

                # Link words_ids to mention as word
                for term in entity_terms:
                    self.link_word(entity, term)
                # Index the entity by its first word
                first_word_id = entity_terms[0]["id"]
                self.mentions_by_word[first_word_id].append(entity)

    def _set_dependencies(self, kaf):
        """ Extract the dependencies of the kaf and add to the graph

        @param kaf: The kaf file manager
        """
        for dependency in kaf.get_dependencies():
            dependency_from = dependency.attrib[READER.DEPENDENCY_FROM_ATTRIBUTE]
            dependency_to = dependency.attrib[READER.DEPENDENCY_TO_ATTRIBUTE]
            dependency_type = dependency.attrib[READER.DEPENDENCY_FUNCTION_ATTRIBUTE]
            #IFS For STANFORD DEPENDENCIES IN KAF
            if dependency_from[0] == "w":
                dependency_from = self.term_by_word_id[dependency_from]
            else:
                dependency_from = self.term_by_id[dependency_from]
            if dependency_to[0] == "w":
                dependency_to = self.term_by_word_id[dependency_to]
            else:
                dependency_to = self.term_by_id[dependency_to]
            self.link_dependency(dependency_from, dependency_to, dependency_type)

    def process_sentence(self, graph, sentence, root_index, sentence_namespace):
        """Add to the graph the morphological, syntactical and dependency info contained in the sentence.

        :param graph: The graph where the kaf info is loaded
        :param sentence: the sentence to parse
        :param sentence_namespace: prefix added to all nodes ID strings.
        :param root_index: The index of the root node
        """
        self.graph = graph
        sentence_id = sentence_namespace
        sentence_label = sentence_namespace

        # Sentence Root
        sentence_root_node = self.add_sentence(root_index=root_index, sentence_form="", sentence_label=sentence_label,
                                               sentence_id=sentence_id)
        sentence_root_node["graph"] = graph
        sentence_root_node["sentence_order"] = self.sentence_order

        first_constituent = self._parse_syntax(sentence=sentence, syntactic_root=sentence_root_node)

        # copy the properties to the root
        if first_constituent != sentence_root_node:
            sentence_root_node["lemma"] = first_constituent["lemma"]
            sentence_root_node["form"] = first_constituent["form"]
            sentence_root_node["span"] = first_constituent["span"]
            sentence_root_node["ord"] = first_constituent["ord"]
            sentence_root_node["begin"] = first_constituent["begin"]
            sentence_root_node["end"] = first_constituent["end"]

        self.sentence_order += 1
        # Statistics
        self.statistics_sentence_up()
        #self.show_graph()
        # Return the generated context graph
        return sentence_root_node

    def _iterate_syntax(self, syntactic_tree, parent, syntactic_root):
        """ Walk recursively over the syntax tree and add their info to the graph.
        @param syntactic_tree: The subtree to process
        @param parent: The parent node of the subtree
        @param syntactic_root: The syntactic root node of all the tree
        @return: The element created from the top of the subtree
        """
        # Aux functions
        def syntax_leaf_process(parent_node, leaf):
            """ Process a final node of the tree
            @param parent_node: The upside node of the element
            @param leaf: The node to process
            @return: The word that correspond to the leaf.
            """
            # the tree node is a leaf
            # Get the text of the tree to obtain more attributes
            self.leaf_count += 1
            text_leaf = leaf.node
            #treebank_word = leaf[0]
            is_head = "=H" in text_leaf or "-H" in text_leaf
            # Get the word node pointed by the leaf
            try:
                word_node = self.terms_pool.pop(0)
                self.last_word = word_node
            except IndexError:
                word_node = self.last_word
            # Word is mark as head
            if is_head:
                self.set_head(parent_node, word_node)
            # Word is mark as Named Entity
            if "|" in text_leaf:
                self.set_ner(constituent=word_node, ner_type=text_leaf.split("|")[-1])
            #Link the word to the node
            self.link_syntax_terminal(parent=parent_node, terminal=word_node)
            #link the word to the sentence
            self.link_root(sentence=syntactic_root, element=word_node)
            self.link_word(sentence=syntactic_root, word=word_node)
            # Enlist entities that appears in the phrase
            for mention in self.entities_by_word.get(word_node["id"], []):
                            self.add_mention_of_named_entity(sentence=syntactic_root, mention=mention)
            # Enlist gold mention that appears in the phrase
            for mention in self.mentions_by_word.get(word_node["id"], []):
                            self.add_mention_of_gold_mention(sentence=syntactic_root, mention=mention)
            return word_node

        def syntax_branch_process(parent_node, branch):
            """ Process a intermediate node of the tree
            @param parent_node: The upside node of the element
            @param branch: The node to process
            @return: The constituent created from the top of the branch
            """
            # Create a node for this element
            label = branch.node
            # constituent is mark as head
            head = "=H" in label or "-H" in label
            tag = label.replace("=H", "").replace("-H", "")
            # Constituent is mark as ner
            if "|" in label:
                ner = label.split("|")[-1]
            else:
                ner = ner_tags.no_ner

            tag = tag.split("|")[0]
            order = self.syntax_count

            new_constituent = self.add_constituent(node_id="C{0}".format(order), sentence=syntactic_root, tag=tag,
                                                   order=order, label=label)
            self.set_ner(new_constituent, ner)
            self.syntax_count += 1
            # Process the children
            children = [
                self._iterate_syntax(
                    syntactic_tree=child, parent=new_constituent, syntactic_root=syntactic_root)
                for child in branch]
            children.sort(key=itemgetter("ord"))

            # Link the child with their parent (The actual processed node)
            self.link_syntax_non_terminal(parent=parent_node, child=new_constituent)
            if head:
                self.set_head(parent_node, new_constituent)
            head_word = self.get_head_word(new_constituent)

            content_text = self._expand_node(children)
            new_constituent["tree"] = branch
            new_constituent["label"] = (u" | ".join((content_text, tag)))
            new_constituent["lemma"] = content_text
            new_constituent["form"] = content_text

            new_constituent[self.doc_type] = head_word[self.doc_type]
            new_constituent["utterance"] = head_word["utterance"]
            new_constituent["quoted"] = head_word["quoted"]
            new_constituent["begin"] = children[0]["begin"]
            new_constituent["end"] = children[-1]["end"]
            new_constituent["ord"] = (children[0]["span"][0], children[-1]["span"][1])
            new_constituent["span"] = new_constituent["ord"]

            # Add in tree named entities to entities in graph
            if constituent_tags.ner_constituent(tag):
                self.add_mention_of_named_entity(sentence=syntactic_root, mention=new_constituent)
                new_constituent["constituent"] = new_constituent

            return new_constituent

        # Determine if the syntactic tree Node is as branch or a leaf
        if len(syntactic_tree) > 1 or not (
                isinstance(syntactic_tree[0], str) or isinstance(syntactic_tree[0], unicode)):
            constituent_or_word = syntax_branch_process(parent_node=parent, branch=syntactic_tree)
            self.syntax_count += 1
        else:
            constituent_or_word = syntax_leaf_process(parent_node=parent, leaf=syntactic_tree)
        return constituent_or_word

    def _parse_syntax_kaf(self, sentence, syntactic_root):
        """ Add the syntax info from a KAF tree node

        @param sentence: The KAF tree element
        @param syntactic_root: The sentence node
        @return: the syntax root node or the first constituent
        """
        #TODO Darle Fuego!!!!!
        constituents_by_id = dict()
        root = None
        root_head = None
        node_process_list = []
        # Build no terminal constituents
        for non_terminal in self.kaf.get_constituent_tree_non_terminals(sentence):
            constituent_id = non_terminal.attrib["id"]
            tag = non_terminal.attrib["label"]
            order = self.syntax_count
            self.syntax_count += 1
            constituent = self.add_constituent(
                node_id=constituent_id, sentence=syntactic_root, tag=tag, order=order, label=tag)
            constituent["ner"] = ner_tags.no_ner
            if constituent_tags.root(tag):
                root = constituent
            constituents_by_id[constituent_id] = constituent
        constituents = list(constituents_by_id.values())
        terminals = self.kaf.get_constituent_tree_terminals(sentence)
        terminals_words = dict()
        # Build Terminals constituents
        for terminal in terminals:
            terminal_id = terminal.attrib["id"]
            node_process_list.append(terminal_id)
            terminals_words[terminal_id] = [
                self.term_by_id[target_term.attrib["id"]]
                for target_term in self.kaf.get_constituent_terminal_words(terminal)]
        # Prepare edges for building tree
        edges_by_departure_node = {}
        edges_list = self.kaf.get_constituent_tree_edges(sentence)
        for edge in edges_list:
            edges_by_departure_node[edge.attrib["from"]] = edge
        if self.secure_tree:
            node_process_list = [edge.attrib["from"] for edge in edges_list]
            node_process_list.reverse()

        while len(node_process_list):
            edge = edges_by_departure_node[node_process_list.pop(0)]
            # The edges have a down-top direction
            target_id = edge.attrib["to"]
            source_id = edge.attrib["from"]
            target = constituents_by_id[target_id]
            # select link type in base of the source node type
            if target != root and not self.secure_tree:
                if target_id not in node_process_list:
                    node_process_list.append(target_id)
            if source_id.startswith("n"):
                source = constituents_by_id[source_id]
                if target == root:
                    if root_head is None or edge.attrib.get("head", False):
                        root_head = source            
                else:
                    self.link_syntax_non_terminal(parent=target, child=source)
                    # Set the head of the constituent
                    if edge.attrib.get("head", False):
                        try:
                            self.set_head(parent=target, head=source)
                        except Exception as ex:
                            self.logger.warning("Error setting a head: Source %s ID#%s Target %s ID#%s Error: %s",
                                                target_id, target, source_id, source, ex)
            else:
                node_process_list.append(target_id)
                source = terminals_words[source_id]
                if target == root:
                    if root_head is None or edge.attrib.get("head", False):
                        root_head = source[0]

                if len(source) == 1 and target["tag"] == source[0][POS]:
                    word = source[0]
                    self.link_root(sentence=syntactic_root, element=word)
                    nexus_constituent = constituents_by_id[target_id]
                    constituents_by_id[target_id] = word
                    self.remove(nexus_constituent)
                    constituents.remove(nexus_constituent)
                    self.link_word(sentence=syntactic_root, word=word)
                    # Enlist entities that appears in the phrase
                    for mention in self.entities_by_word.get(word["id"], []):
                        self.add_mention_of_named_entity(sentence=syntactic_root, mention=mention)
                    for mention in self.mentions_by_word.get(word["id"], []):
                        self.add_mention_of_gold_mention(sentence=syntactic_root, mention=mention)
                else:
                    for word in source:
                        self.link_root(sentence=syntactic_root, element=word)
                        self.link_syntax_terminal(parent=target, terminal=word)
                        self.link_word(sentence=syntactic_root, word=word)
                        # Enlist entities that appears in the phrase
                        for mention in self.entities_by_word.get(word["id"], []):
                            self.add_mention_of_named_entity(sentence=syntactic_root, mention=mention)
                        # Enlist gold mentions that appears in the phrase
                        for mention in self.mentions_by_word.get(word["id"], []):
                            self.add_mention_of_gold_mention(sentence=syntactic_root, mention=mention)
                        # Set the head of the constituent
                    self.set_head(target, source[-1])

        # Build constituent child based values
        for constituent in constituents:
            if constituent == root:
                continue
            children = self.get_words(constituent)
            children.sort(key=itemgetter("ord"))
            head_word = self.get_head_word(constituent)
            content_text = self._expand_node(children)
            constituent[self.doc_type] = head_word[self.doc_type]
            constituent["utterance"] = head_word["utterance"]
            constituent["quoted"] = head_word["quoted"]
            constituent["label"] = (" | ".join((content_text, constituent["tag"])))
            constituent["lemma"] = self._expand_node_lemma(children)
            constituent["form"] = content_text
            constituent["begin"] = children[0]["begin"]
            constituent["end"] = children[-1]["end"]
            constituent["ord"] = (children[0]["span"][0], children[-1]["span"][1])
            constituent["span"] = constituent["ord"]

        # link the tree with the root
        if root_head is None:
            self.logger.warning("No ROOT found, used the first constituent, sentence: %s",
                                syntactic_root["sentence_order"])
            root_head = constituents[0]

        self.link_syntax_non_terminal(parent=syntactic_root, child=root_head)
        # Set the head of the constituent
        self.set_head(syntactic_root, root_head)
        return root_head

    def _parse_syntax(self, sentence, syntactic_root):
        """ Parse the syntax of the sentence.

        @param sentence:  The sentence
        @param syntactic_root:
        @return: The upper node of the syntax tree.
        """
        # Convert the syntactic tree
        if type(sentence) is str:
            # Is a plain Penn-tree
            sentence = self.clean_penn_tree(sentence)
            syntactic_tree = tree.Tree(sentence)
            # Call to the recursive function
            return self._iterate_syntax(
                syntactic_tree=syntactic_tree, parent=syntactic_root, syntactic_root=syntactic_root)
        else:
            # Is a kaf tree
            return self._parse_syntax_kaf(sentence=sentence, syntactic_root=syntactic_root)

    # AUX FUNCTIONS
    @staticmethod
    def _expand_kaf_word(words):
        """ Rebuild the text form from a list of kaf words
        @param words: a list of KAF words
        @return: the form of all words separated by comas.
        """
        text = " ".join([word.text for word in words])
        return text.strip()

    @staticmethod
    def _expand_node(terms):
        """ Rebuild the from of a element
        @param terms: The ordered term lsit of this element
        @return: The form of the element
        """
        text = " ".join([str(term["form"]) for term in terms])
        return text.strip()

    @staticmethod
    def _expand_node_lemma(terms):
        """ Rebuild the lemma of a element
        @param terms: The ordered term list of this element
        @return: The form of the element
        """
        text = " ".join([str(term["lemma"]) for term in terms])
        return text.strip()

    @staticmethod
    def clean_penn_tree(penn_tree):
        """ Clean from the tree all knows problems
        @param penn_tree: the plain tree
        @return: cleaned tree
        """
        penn_tree = penn_tree.strip()
        return penn_tree