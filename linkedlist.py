from manim import *

class LinkedListNode(VGroup):
    def __init__(self, data, address=None, width=0.6, height=0.3, data_color=WHITE, address_color=PINK, **kwargs):
        super().__init__(**kwargs)

        data_rect = Rectangle(width=width, height=height / 2, color=data_color, fill_opacity=0.7)
        address_rect = Rectangle(width=width, height=height / 2, color=address_color, fill_opacity=0.7)

        data_text = Text(f"Data: {data}", color=BLACK, background_stroke_width=0, font_size=15)
        address_text = Text(f"Address: ", color=BLACK, background_stroke_width=0, font_size=15)
        my_address=Text(address,color=WHITE, background_stroke_width=0, font_size=15)

        data_text.move_to(data_rect, ORIGIN)
        address_text.move_to(address_rect, LEFT)
        my_address.next_to(address_rect,3*DOWN)

        data_rect_group = VGroup(data_rect, data_text)
        address_rect_group = VGroup(address_rect, address_text)

        address_rect_group.next_to(data_rect_group, DOWN, buff=0)
        self.my_address=my_address
        self.address_text=address_text
        self.add(data_rect_group, address_rect_group,my_address)

class LinkedList(Scene):
    def construct(self):
        title = Text("Linked List Creation", color=WHITE, font_size=28)
        title.move_to([0, 3.2, 0])
        self.play(Write(title))
        print("Enter the numbers separated by space")
        values = list(map(int, input().split()))
        nums = len(values)
        node_width = 10 / nums
        node_height = 4 / nums
        distance = node_width / 3
        linked_list = self.create_linked_list(values, node_width, node_height, distance)
        # self.play(*[Create(node) for node in linked_list], run_time=0.5)
        self.wait(1)

    def create_linked_list(self, values, node_width, node_height, distance):
        nodes = VGroup()
        linked_list = VGroup()
        head = LinkedListNode(data="headnode", address="0x000", width=node_width, height=node_height)
        head.move_to([-7 + node_width * (0 + 1 / 2), -2, 0])
        self.play(Create(head))

        for i, value in enumerate(values):
            address = f"0x{i + 1:04X}"
            node = LinkedListNode(data=value, address=address, width=node_width, height=node_height)
            nodes.add(node)
            linked_list.add(node)
            node.move_to([0, -2, 0])
            self.play(Create(node))
            if i == 0:
                self.play(node.animate.move_to([-7 + node_width * (0 + 1 / 2), 0, 0]))
                self.play(node.my_address.copy().animate.next_to(head.address_text,RIGHT))
                arrow = Arrow(start=head.get_top(),end=head.get_top()+[0,1,0]).next_to(head,UP,buff=0)
                self.play(Create(arrow))
                # arrow = Arrow(start=node.get_right(),end=node.get_right()+[distance,0,0]).next_to(node,RIGHT)
                # self.play(Create(arrow))
                
            elif nodes:
                self.play(node.animate.next_to(nodes[-2], RIGHT, buff=distance))
                self.play(nodes[-1].my_address.copy().animate.next_to(nodes[-2].address_text,RIGHT))
                arrow = Arrow(start=nodes[-2].get_right(),end=nodes[-1].get_left()+[0.6*distance,0,0]).next_to(nodes[-2],RIGHT,buff=0)
                self.play(Create(arrow))
                

            

        return linked_list

if __name__ == "__main__":
    module_name = os.path.basename(__file__)
    command = " ".join(["manim", "-pqh", module_name, "LinkedList"])
    os.system(command)